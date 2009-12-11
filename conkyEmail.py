#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
# conkyEmail.py is a simple python script to gather 
# details of email inboxes use in conky.
#
# Author: Kaivalagi
# Created: 16/05/2008
#
#Modified:
#    25/08/2008    Switched to using "UNSEEN" IMAP search filter instead of "RECENT"
#    25/08/2008    Added mailinfo feature for both POP and IMAP, details of the from address and subject are output if requested, option ignored in template mode!
#    25/08/2008    Connection timeouts are valid in the template now
#    26/08/2008    Tidied up mailinfo output, removed trailing email address from !from" and put in numbers
#    27/08/2008    Updated regex for date stripping to handle unratified email data (thanks yahoo)
#    29/08/2008    Added header decoding for sender and subject, to handle multiple character sets used
#    02/09/2008    Updated regex to use groups now to pick out the date from the recieved date string, should cope with all timezone data in mail message (+0100 or GMT)
#    03/09/2008    Updated error and info handling and logging
#    04/09/2008    Fixed bug with template based output
#    04/09/2008    Added --version option to output version of script and exit
#    02/10/2008    Updated script to use new template methods from conkyForecast
#    02/10/2008    Updated script to now use "[" and "]" as template brackets rather than "{" and "}" so that the execp/execpi conky command can be used, this enables the use of $font, $color options in the template which conky will then make adjustments for in the output!
#    02/10/2008    Added mailinfo option to template functionality
#    04/10/2008    Updated help for template option
#    20/10/2008    Updated date regex to cope better with message date text -> date variable conversion, will mean sorting is correct now
#    25/10/2008    Changed imap fetch to use '(BODY.PEEK[HEADER])' option rather than '(RFC822)' in an attempt to stop marking items as read
#    28/10/2008    Added folder option for imap emails, so a folder can be specified, if not set the default "Inbox" is used.
#    03/11/2008    Updated code to cope with varied message date formats, no one seems to follow the rfcs!
#    10/11/2008    Added --errorlog and --infolog options to log data to a file
#    24/11/2008    Updated to convert mailinfo and connectiontimeout to correct datatype to stop strange behaviour
#    02/01/2009    Fixed email sort to be reversed so newest is first
#    14/01/2009    Use default values for message date/subject/sender if nothing can be obtained from the email headers, there should always be a date value and the sort should work regardless of the email date format...
#    01/03/2009    Added --maxwidth option to wrap text to set widths, and --nowrap to only output one line of mailinfo
#    16/03/2008    Added --port option to use alternative port numbers other than the defaults
#    29/03/2009    Added traceback calls in error handling to get more info and updated sort method to handle no recvdate
import sys, poplib, imaplib, socket, re, textwrap, traceback
from optparse import OptionParser
from datetime import *
from email.header import decode_header

class CommandLineParser:

    parser = None

    def __init__(self):

        self.parser = OptionParser()
        self.parser.add_option("-m","--servertype", dest="servertype", default="POP", type="string", metavar="SERVERTYPE", help=u"servertype to check [default: %default] The server type options are POP or IMAP")
        self.parser.add_option("-s","--servername", dest="servername", default="pop.mail.yahoo.co.uk", type="string", metavar="SERVERNAME", help=u"server name to access [default: %default] The server name should be either a domain name or ip address")
        self.parser.add_option("-o","--port",dest="port", type="int", metavar="NUMBER", help=u"Define an alternative port number to use other than the default for the protocol/ssl")
        self.parser.add_option("-f","--folder",dest="folder", type="string", metavar="FOLDER", default="Inbox", help=u"[default: %default] IMAP folder to check, not applicable for POP mail checks")
        self.parser.add_option("-e","--ssl", dest="ssl", default=False, action="store_true", help=u"Use an SSL based connection.")
        self.parser.add_option("-u","--username",dest="username", type="string", metavar="USERNAME", help=u"username to login with")
        self.parser.add_option("-p","--password",dest="password", type="string", metavar="PASSWORD", help=u"Password to login with")
        self.parser.add_option("-t","--template",dest="template", type="string", metavar="FILE", help=u"define a template file to generate output in one call. A displayable item in the file is in the form [--servertype=IMAP --ssl --servername=imap.gmail.com --folder=Inbox --username=joebloggs --password=letmein, --connectiontimeout=10]. Note that the short forms of the options are not currently supported! None of these options are applicable at command line when used in templates.")
        self.parser.add_option("-i","--mailinfo", dest="mailinfo", type="int", default=0, metavar="NUMBER", help=u"[default: %default] The number of newest emails to output 'from' and 'subject' information for. Not applicable at command line when using templates.")
        self.parser.add_option("-w","--maxwidth",dest="maxwidth", default=80, type="int", metavar="NUMBER", help=u"[default: %default] Define the number of characters to output per line")
        self.parser.add_option("-l","--linelimit", dest="linelimit", default=0, type="int", metavar="NUMBER", help=u"[default: %default] If above zero this limits the number of lines output for mail info")
        self.parser.add_option("-q","--quote", dest="quote", default="\"", type="string", metavar="CHAR", help=u"[default: %default] The character to use for quotations around the subject line")
        self.parser.add_option("-c","--connectiontimeout",dest="connectiontimeout", type="int", default=10, metavar="NUMBER", help=u"[default: %default] Define the number of seconds before a connection timeout can occur. Not applicable at command line when using templates.")
        self.parser.add_option("-v","--verbose", dest="verbose", default=False, action="store_true", help=u"request verbose output, not a good idea when running through conky!")
        self.parser.add_option("-V", "--version", dest="version", default=False, action="store_true", help=u"Displays the version of the script.")
        self.parser.add_option("--errorlogfile", dest="errorlogfile", type="string", metavar="FILE", help=u"If a filepath is set, the script appends errors to the filepath.")
        self.parser.add_option("--infologfile", dest="infologfile", type="string", metavar="FILE", help=u"If a filepath is set, the script appends info to the filepath.")        

    def parse_args(self):
        (options, args) = self.parser.parse_args()
        return (options, args)

    def print_help(self):
        return self.parser.print_help()

class EmailData:
    def __init__(self, servername, folder, username, num, sender, subject, recvdate, messageid):
        self.servername = servername
        self.folder = folder
        self.username = username
        self.num = num
        self.sender = sender
        self.subject = subject
        self.recvdate = recvdate
        self.messageid = messageid

    def __cmp__(self, other):
        return cmp(self.getRecvDate(self.recvdate), self.getRecvDate(other.recvdate))
    
    def getRecvDate(self, recvdate):
        if recvdate is None:
            return datetime.now()
        else:
            return recvdate
        
class EmailInfo:

    IMAP_SEARCH_OPTION = "UNSEEN" # "RECENT"
    POP_FETCH_OPTION = "TOP" # "RETR"
    
    emaillist = []

    def __init__(self,options):

        self.options = options

    def getTemplateList(self,template):

        templatelist = []
    
        for template_part in template.split("{"):
            if template_part != "":
                for template_part in template_part.split("}"):
                    if template_part != "":
                        templatelist.append(u""+template_part)

        return templatelist

    def getOutputData(self,servertype,servername,port,folder,ssl,username,password,connectiontimeout,mailinfo):
        try:
            output = u""
            
            socket.setdefaulttimeout(connectiontimeout)
        
            if servertype == "POP":
                count = self.getPOPEmailData(servername,port,folder,ssl,username,password,mailinfo)
            elif servertype == "IMAP":
                count = self.getIMAPEmailData(servername,port,folder,ssl,username,password,mailinfo)
            else:
                if self.options.verbose == True:
                    self.logError("Unknown server type of %s requested"%servertype)

            if count == -1:
                output = "?"
            elif count == 0:
                output = "0"
            else:
                
                if mailinfo > 0:

                    output = "%s New"%count
                    
                    counter = 0
                    self.emaillist.sort(reverse=True)
                    for emaildata in self.emaillist:
                        counter = counter + 1
                        if mailinfo >= counter:
                            bullet = "%s. "%(counter)
                            
                            text = "%s: %s%s%s"%(emaildata.sender,self.options.quote,emaildata.subject,self.options.quote)
                            text = bullet + self.getWrappedText(text, self.options.maxwidth, len(bullet), self.options.linelimit)
                            output = output + "\n" + text
                 
                else:
                    output = str(count)
                    
            return output

        except Exception, e:
            self.logError("getOutputData:Unexpected error:" + traceback.format_exc())      
            return "?"

    def getTemplateItemOutput(self, template_text):
        
        # keys to template data
        SERVERTYPE_KEY = "servertype"
        SERVERNAME_KEY = "servername"
        PORT_KEY = "port"
        FOLDER_KEY = "folder"
        SSL_KEY= "ssl"
        USERNAME_KEY = "username"
        PASSWORD_KEY = "password"
        CONNECTION_TIMEOUT_KEY = "connectiontimeout"
        MAILINFO_KEY = "mailinfo"
        
        servertype = self.options.servertype
        servername = None
        port = None
        folder = self.options.folder
        ssl = self.options.ssl
        username = None
        password = None
        connectiontimeout = self.options.connectiontimeout
        mailinfo = self.options.mailinfo
        
        for option in template_text.split('--'):
            if len(option) == 0 or option.isspace():
                continue
            
            # not using split here...it can't assign both key and value in one call, this should be faster
            x = option.find('=')
            if (x != -1):
                key = option[:x].strip()
                value = option[x + 1:].strip()
                if value == "":
                    value = None
            else:
                key = option.strip()
                value = None
                    
            try:
                if key == SERVERTYPE_KEY:
                    servertype = value
                elif key == SERVERNAME_KEY:
                    servername = value
                elif key == PORT_KEY:
                    port = int(value)
                elif key == FOLDER_KEY:
                    folder = value                    
                elif key == SSL_KEY:
                    ssl = True
                elif key == USERNAME_KEY:
                    username = value
                elif key == PASSWORD_KEY:
                    password = value
                elif key == CONNECTION_TIMEOUT_KEY:
                    connectiontimeout = int(value)
                elif key == MAILINFO_KEY:
                    mailinfo = int(value)                                                   
                else:
                    self.logError("Unknown template option: " + option)

            except (TypeError, ValueError):
                self.logError("Cannot convert option argument to number: " + option)
                return u""
                
        if servername != None:
            return self.getOutputData(servertype,servername,port,folder,ssl,username,password,connectiontimeout,mailinfo)
        else:
            self.logError("Template item does not have servername defined")
            return u""


    def getOutputFromTemplate(self, template):
        output = u""
        end = False
        a = 0
        
        # a and b are indexes in the template string
        # moving from left to right the string is processed
        # b is index of the opening bracket and a of the closing bracket
        # everything between b and a is a template that needs to be parsed
        while not end:
            b = template.find('[', a)
            
            if b == -1:
                b = len(template)
                end = True
            
            # if there is something between a and b, append it straight to output
            if b > a:
                output += template[a : b]
                # check for the escape char (if we are not at the end)
                if template[b - 1] == '\\' and not end:
                    # if its there, replace it by the bracket
                    output = output[:-1] + '['
                    # skip the bracket in the input string and continue from the beginning
                    a = b + 1
                    continue
                    
            if end:
                break
            
            a = template.find(']', b)
            
            if a == -1:
                self.logError("Missing terminal bracket (]) for a template item")
                return u""
            
            # if there is some template text...
            if a > b + 1:
                output += self.getTemplateItemOutput(template[b + 1 : a])
            
            a = a + 1

        return output

    def getEmailData(self,servername,folder,username,num,lines):
        
        try:
            self.logInfo("Processing email data to determine 'From', 'Subject' and 'Received Date'")
                            
            sender = None
            subject = None
            recvdate = None
            messageid = None
            
            for line in lines:
                if sender is None and line.find("From: ") >= 0:
                    text = line.replace("From: ","").strip("\r ")
                    try:
                        text = self.decodeHeader(text)
                    except Exception, e:
                        sender = text
                        self.logError("getEmailData:Unexpected error when decoding sender:" + e.__str__()) 
                    sender = re.sub('<.*?@.*?>','',text).strip().lstrip('"').rstrip('"') # remove trailing email in <>
                    if sender is None:
                        sender = "Unknown"
                elif subject is None and line.find("Subject: ") >= 0:
                    text = line.replace("Subject: ","").strip("\r\" ")
                    try:
                        subject = self.decodeHeader(text)
                    except Exception, e:
                        subject = text
                        self.logError("getEmailData:Unexpected error when decoding subject:" + e.__str__())
                    if subject is None:
                        subject = "Unknown"
                elif recvdate is None and line.find("Date: ") >= 0:
                    text = line.replace("Date: ","").strip("\r ")
                    try:
                        text = re.match(r"(.*\s)(\d{1,2}\s\w{3}\s\d{4}\s\d{1,2}:\d{1,2}:\d{1,2})(\s.*)"," "+text+" ").group(2) # intentional space at the front and back of text to allow for groups when missing
                        recvdate = datetime.strptime(text,"%d %b %Y %H:%M:%S") # convert to proper datetime
                    except Exception, e:
                        recvdate = datetime.now()
                        self.logError("getEmailData:Unexpected error when converting receive date to datetime:" + e.__str__())
                elif messageid is None and line.find("Message-ID: ") >= 0:
                    text = line.replace("Message-ID: ","").strip("\r ")
                    messageid = text
                    if messageid is None:
                        messageid = 0

                if sender is not None and \
                   subject is not None and \
                   recvdate is not None and \
                   messageid is not None:                    
                    break

            if subject is None:
                subject = ""
                                            
            emaildata = EmailData(servername, folder, username, num, sender, subject, recvdate, messageid)
                
            return emaildata

        except Exception, e:
            self.logError("getEmailData:Unexpected error:" + traceback.format_exc())  
            return None
        
    def getPOPEmailData(self,servername,port,folder,ssl,username,password,mailinfo):

        try:

            self.logInfo("Logging on to POP server: "+ servername)
            
            if port == None:
                if ssl == True:
                    pop = poplib.POP3_SSL(servername)
                else:
                    pop = poplib.POP3(servername)            
            else:
                if ssl == True:
                    pop = poplib.POP3_SSL(servername, port)
                else:
                    pop = poplib.POP3(servername, port)                    
                
            pop.user(username)
            pop.pass_(password)
            
            self.logInfo("Getting message count from POP server: "+ servername)
                            
            count = len(pop.list()[1])
            
            if count > 0 and mailinfo > 0:
            
                self.logInfo("Extracting message data from POP server \"%s\""%servername)

                self.emaillist = []
                
                for num in range(count):
                    
                    if self.POP_FETCH_OPTION == "TOP":
                        lines = pop.top(num+1,1)[1]
                    else:
                        lines = pop.retr(num+1,1)[1] #more robust but sets message as seen!
                    
                    emaildata = self.getEmailData(servername,folder,username,num,lines)
                    
                    if emaildata is not None:
                        self.emaillist.append(emaildata)
                
            self.logInfo("Logging off from POP server: "+ servername)
                
            pop.quit()
            
            return count
        
        except Exception, e:
            self.logError("getPOPEmailData:Unexpected error:" + traceback.format_exc())
            return -1

    def getIMAPEmailData(self,servername,port,folder,ssl,username,password,mailinfo):

        try:
            
            self.logInfo("Logging on to IMAP server: "+ servername)
            
            if port == None:
                if ssl == True:
                    imap = imaplib.IMAP4_SSL(servername)
                else:
                    imap = imaplib.IMAP4(servername)
            else:
                if ssl == True:
                    imap = imaplib.IMAP4_SSL(servername, port)
                else:
                    imap = imaplib.IMAP4(servername, port)
                                
            imap.login(username, password)

            self.logInfo("Searching for new mail on IMAP server \"%s\" in folder \"%s\""%(servername,folder))
                
            imap.select(folder)
            typ, data = imap.search(None, self.IMAP_SEARCH_OPTION)
            for item in data:
                if item == '':
                    data.remove(item)

            if len(data) > 0:
                nums = data[0].split()
                count = (len(nums))
            else:
                count = 0
            
            if count > 0 and mailinfo > 0:

                self.logInfo("Extracting message data for IMAP server: "+ servername)
                
                self.emaillist = []
                                
                for num in nums:
                    typ, message = imap.fetch(num, '(BODY.PEEK[HEADER])')
                    lines = message[0][1].split("\n") # grab the content we want and split out lines
                    
                    emaildata = self.getEmailData(servername,folder,username,num,lines)
                    
                    if emaildata is not None:
                        self.emaillist.append(emaildata)
                        
            self.logInfo("Logging of from IMAP server: "+ servername)
                    
            imap.close()
            imap.logout()
            imap.shutdown()
    
            return count
    
        except Exception, e:
            self.logError("getIMAPEmailData:Unexpected error:" + traceback.format_exc())
            return -1
        
    def writeOutput(self):

        if self.options.template != None:
            #load the file
            try:
                fileinput = open(self.options.template)
                template = fileinput.read()
                fileinput.close()
            except Exception, e:
                self.logError("Error loading template file: " + e.__str__())
            else:
                output = self.getOutputFromTemplate(template)
        else:
            output = self.getOutputData(self.options.servertype,self.options.servername,self.options.port,self.options.folder,self.options.ssl,self.options.username,self.options.password,self.options.connectiontimeout,self.options.mailinfo)

        print output.encode("utf-8")

    def decodeHeader(self,header_text):
        
        text,encoding = decode_header(header_text)[0]
        if encoding:
            try:
                return text.decode(encoding)
            except: # fallback on decode error to windows encoding as this may be introduced by sloppy mail clients
                return text.decode('cp1252')
        else:
            return text
        
    def getWrappedText(self,text,width=40,indent=0,linelimit=0):
        if len(text) > width:
            wrappedtext = ""
            indentchars = "".ljust(indent)
            linecount = 0
            lines = textwrap.wrap(text,width=width,expand_tabs=False,replace_whitespace=False,subsequent_indent=indentchars)
            for line in lines:
                linecount = linecount + 1
                if linelimit == 0 or linecount <= linelimit:
                    wrappedtext = wrappedtext + line + "\n"
                else:
                    break
            return wrappedtext.rstrip("\n ")
        else:
            return text        
            
    def logInfo(self, text):
        if self.options.verbose == True:
            print >> sys.stdout, "INFO: " + text

        if self.options.infologfile != None:
            datetimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            fileoutput = open(self.options.infologfile, "ab")
            fileoutput.write(datetimestamp+" INFO: "+text+"\n")
            fileoutput.close()
            
    def logError(self, text):
        print >> sys.stderr, "ERROR: " + text
        
        if self.options.errorlogfile != None:
            datetimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            fileoutput = open(self.options.errorlogfile, "ab")
            fileoutput.write(datetimestamp+" ERROR: "+text+"\n")
            fileoutput.close()
        
def main():

    parser = CommandLineParser()
    (options, args) = parser.parse_args()

    if options.version == True:
        
        print >> sys.stdout,"conkyEmail v.2.06"
        
    else:
        
        if options.verbose == True:
            print >> sys.stdout, "*** INITIAL OPTIONS:"
            print >> sys.stdout, "    servertype:",options.servertype
            print >> sys.stdout, "    servername:",options.servername
            print >> sys.stdout, "    port:",options.port
            print >> sys.stdout, "    folder:",options.folder
            print >> sys.stdout, "    ssl:",options.ssl
            print >> sys.stdout, "    username:",options.username
            print >> sys.stdout, "    password:",options.password
            print >> sys.stdout, "    template:",options.template
            print >> sys.stdout, "    mailinfo:",options.mailinfo
            print >> sys.stdout, "    maxwidth:",options.maxwidth
            print >> sys.stdout, "    linelimit:",options.linelimit
            print >> sys.stdout, "    quote:",options.quote
            print >> sys.stdout, "    verbose:",options.verbose
            print >> sys.stdout, "    errorlogfile:",options.errorlogfile
            print >> sys.stdout, "    infologfile:",options.infologfile            
    
        # create new global weather object
        emailinfo = EmailInfo(options)
        emailinfo.writeOutput()
    
if __name__ == '__main__':
    main()
    sys.exit()
