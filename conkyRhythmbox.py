#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
# conkyRhythmbox.py is a simple python script to gather 
# details of from Rhythmbox for use in conky.
#
#  Author: Kaivalagi
# Created: 23/09/2008
# Modifications:
#    25/09/2008    Updated to handle when no music is playing, no unnecessary dbus calls will be made
#    25/09/2008    Updated rating output generation to use ljust string function
#    02/10/2008    Updated script to now use "[" and "]" as template brackets rather than "{" and "}" so that the execp/execpi conky command can be used, this enables the use of $font, $color options in the template which conky will then make adjustments for in the output!
#    04/10/2008    Updated help for template option
#    08/11/2008    Added genre to the datatypes, used with --datatype=GE
#    08/11/2008    Added stream support, to display what is available and not crash
#    10/11/2008    Added --errorlog and --infolog options to log data to a file, and removed unnecessary --enableerrors option
#    15/11/2008    Now loading the template file in unicode mode to allow for the extended character set
#    17/11/2008    Added datatypes: ST (status), GE (genre), YR (year), TN (track number), FN (file name)
#    17/11/2008    Added --statustext option to allow overridding of the standard status text
#    20/11/2008    Unrated rating now outputs nothing
#    21/11/2008    Fixed statustext to work inside template now
#    31/12/2008    Fixed track number output (--datatype=TN)
#    06/01/2009    Removed .encode("utf-8") from internal return to fix unicode output?...it works...

#    14/01/2009    Updated to handle CD and last.fm music sources better
#    14/01/2009    Added --maxlength option for command line and templates, to limit string output if need be
#    18/05/2009    Updated to expand ~ based template paths
from datetime import datetime
from optparse import OptionParser
import sys
import traceback
import codecs
import os
try:
    import dbus
    DBUS_AVAIL = True
except ImportError:
    # Dummy D-Bus library
    class _Connection:
        get_object = lambda *a: object()
    class _Interface:
        __init__ = lambda *a: None
        ListNames = lambda *a: []
    class Dummy: pass
    dbus = Dummy()
    dbus.Interface = _Interface
    dbus.service = Dummy()
    dbus.service.method = lambda *a: lambda f: f
    dbus.service.Object = object
    dbus.SessionBus = _Connection
    DBUS_AVAIL = False


class CommandLineParser:

    parser = None

    def __init__(self):

        self.parser = OptionParser()
        self.parser.add_option("-t", "--template", dest="template", type="string", metavar="FILE", help=u"define a template file to generate output in one call. A displayable item in the file is in the form [--datatype=TI]. The following are possible options within each item: --datatype,--ratingchar. Note that the short forms of the options are not currently supported! None of these options are applicable at command line when using templates.")
        self.parser.add_option("-d", "--datatype", dest="datatype", default="TI", type="string", metavar="DATATYPE", help=u"[default: %default] The data type options are: ST (status), TI (title), AL (album), AR (artist), GE (genre), GE (genre), YR (year), TN (track number), FN (file name), LE (length), PP (current position in percent), PT (current position in time), VO (volume), RT (rating). Not applicable at command line when using templates.")
        self.parser.add_option("-r", "--ratingchar", dest="ratingchar", default="*", type="string", metavar="CHAR", help=u"[default: %default] The output character for the ratings scale. Command line option overridden if used in templates.")
        self.parser.add_option("-s", "--statustext", dest="statustext", default="Playing,Paused,Stopped", type="string", metavar="TEXT", help=u"[default: %default] The text must be comma delimited in the form 'A,B,C'. Command line option overridden if used in templates.")
        self.parser.add_option("-n", "--nounknownoutput", dest="nounknownoutput", default=False, action="store_true", help=u"Turn off unknown output such as \"Unknown\" for title and \"0:00\" for length. Command line option overridden if used in templates.")
        self.parser.add_option("-m", "--maxlength", dest="maxlength", default="0", type="int", metavar="LENGTH", help=u"[default: %default] Define the maximum length of any datatypes output, if truncated the output ends in \"...\"")
        self.parser.add_option("-v", "--verbose", dest="verbose", default=False, action="store_true", help=u"Request verbose output, not a good idea when running through conky!")
        self.parser.add_option("-V", "--version", dest="version", default=False, action="store_true", help=u"Displays the version of the script.")
        self.parser.add_option("--errorlogfile", dest="errorlogfile", type="string", metavar="FILE", help=u"If a filepath is set, the script appends errors to the filepath.")
        self.parser.add_option("--infologfile", dest="infologfile", type="string", metavar="FILE", help=u"If a filepath is set, the script appends info to the filepath.")                

    def parse_args(self):
        (options, args) = self.parser.parse_args()
        return (options, args)

    def print_help(self):
        return self.parser.print_help()

class MusicData:
    def __init__(self,status,coverart,title,album,length,artist,tracknumber,genre,year,filename,current_position_percent,current_position,rating,volume):
        self.status = status
        self.coverart = coverart
        self.title = title
        self.album = album
        self.length = length
        self.artist = artist
        self.tracknumber = tracknumber
        self.genre = genre
        self.year = year
        self.filename = filename        
        self.current_position_percent = current_position_percent
        self.current_position = current_position
        self.rating = rating
        self.volume = volume
        
        
class RhythmboxInfo:
    
    error = u""
    musicData = None
    
    def __init__(self, options):
        self.options = options
        
    def testDBus(self, bus, interface):
        obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        dbus_iface = dbus.Interface(obj, 'org.freedesktop.DBus')
        avail = dbus_iface.ListNames()
        return interface in avail
        
    def getOutputData(self, datatype, ratingchar, statustext, nounknownoutput, maxlength):
        output = u""
        
        if nounknownoutput == True:
            unknown_time = ""
            unknown_number = ""
            unknown_string = ""
        else:
            unknown_time = "0:00"
            unknown_number = "0"
            unknown_string = "Unknown"
        
        try:
                
            bus = dbus.SessionBus()
            if self.musicData == None:
                
                if self.testDBus(bus, 'org.gnome.Rhythmbox'):
                
                    self.logInfo("Calling dbus interface for music data")
    
                    try:
                        self.logInfo("Setting up dbus interface")
                        
                        # setup dbus hooks
                        remote_object_shell = bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Shell')
                        iface_shell = dbus.Interface(remote_object_shell, 'org.gnome.Rhythmbox.Shell')
                        remote_object_player = bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Player')
                        iface_player = dbus.Interface(remote_object_player, 'org.gnome.Rhythmbox.Player')
                            
                        self.logInfo("Calling dbus interface for music data")
                        
                        # prepare song properties for data retrieval
                        
                        volume = str(int(100*iface_player.getVolume()))
                        
                        uri = iface_player.getPlayingUri()
                        if len(uri) == 0:
                            status = self.getStatusText("stopped", statustext)
                            self.musicData = MusicData(status,None,None,None,None,None,None,None,None,None,None,None,None,volume)
                        else:
                            status = self.getStatusText("playing", statustext)
                            
                            props = iface_shell.getSongProperties(uri)

                            # grab the data into variables
                            location = props["location"]
                            
                            # handle a file or stream differently for filename
                            if location.find("file://") != -1:
                                filename = location[location.rfind("/")+1:]  
                            elif len(location) > 0:
                                filename = location
                            else:
                                filename = ""
                            
                            # try to get all the normal stuff...the props return an empty string if nothing is available
                            title = props["title"]
                            album = props["album"]
                            artist = props["artist"]
                            year = str(props["year"])
                            tracknumber = str(props["track-number"])

                            if year == "0": year = "?"
                            if tracknumber == "0": tracknumber = "?"
                            
                            # if no title and a stream song title then use that instead (internet radio)
                            if len(title) == 0 and "rb:stream-song-title" in props:
                                title = props["rb:stream-song-title"]

                            # get coverart url or file link
                            coverart = ""
                            if "rb:coverArt-uri" in props:
                                coverart = props["rb:coverArt-uri"]
                                if coverart.find("http://") != -1:
                                    coverart = ""
                                else:
                                    coverart = coverart.replace("file://","")

                                #handle escape chars, are there anymore???
                                coverart = coverart.replace(" ", "\ ")
                                coverart = coverart.replace("(", "\(")
                                coverart = coverart.replace(")", "\)")
                                    
                            # common details                 
                            genre = props["genre"]                            
                            length_seconds = int(props["duration"])
                            current_seconds = int(iface_player.getElapsed())
                            current_position = str(int(current_seconds/60%60)).rjust(1,"0")+":"+str(int(current_seconds%60)).rjust(2,"0")
                            
                            if length_seconds > 0:
                                length = str(length_seconds/60%60).rjust(1,"0")+":"+str(length_seconds%60).rjust(2,"0")
                                current_position_percent = str(int((float(current_seconds) / float(props["duration"]))*100)) 
                            else:
                                length = "0:00"
                                current_position_percent = "0"
                                
                            rating = str(int(props["rating"]))
                                                
                            self.musicData = MusicData(status,coverart,title,album,length,artist,tracknumber,genre,year,filename,current_position_percent,current_position,rating,volume)                           
                            
                    except Exception, e:
                        self.logError("Issue calling the dbus service:"+e.__str__())

            if self.musicData != None:
                
                self.logInfo("Preparing output for datatype:"+datatype)

                if datatype == "ST": #status
                    if self.musicData.status == None or len(self.musicData.status) == 0:
                        output = None
                    else:
                        output = self.musicData.status

                elif datatype == "CA": #coverart
                    if self.musicData.coverart == None or len(self.musicData.coverart) == 0:
                        output = None
                    else:
                        output = self.musicData.coverart
                            
                elif datatype == "TI": #title
                    if self.musicData.title == None or len(self.musicData.title) == 0:
                        output = None
                    else:
                        output = self.musicData.title
                        
                elif datatype == "AL": #album
                    if self.musicData.album == None or len(self.musicData.album) == 0:
                        output = None
                    else:
                        output = self.musicData.album
                        
                elif datatype == "AR": #artist
                    if self.musicData.artist == None or len(self.musicData.artist) == 0:
                        output = None
                    else:
                        output = self.musicData.artist

                elif datatype == "TN": #tracknumber
                    if self.musicData.tracknumber == None or len(self.musicData.tracknumber) == 0:
                        output = None
                    else:
                        output = self.musicData.tracknumber
                        
                elif datatype == "GE": #genre
                    if self.musicData.title == genre or len(self.musicData.genre) == 0:
                        output = None
                    else:
                        output = self.musicData.genre
                        
                elif datatype == "YR": #year
                    if self.musicData.year == None or len(self.musicData.year) == 0:
                        output = None
                    else:
                        output = self.musicData.year
                                                
                elif datatype == "FN": #filename
                    if self.musicData.filename == None or len(self.musicData.filename) == 0:
                        output = None
                    else:
                        output = self.musicData.filename

                elif datatype == "LE": # length
                    if self.musicData.length == None or len(self.musicData.length) == 0:
                        output = None
                    else:
                        output = self.musicData.length
                        
                elif datatype == "PP": #current position in percent
                    if self.musicData.current_position_percent == None or len(self.musicData.current_position_percent) == 0:
                        output = None
                    else:
                        output = self.musicData.current_position_percent
                        
                elif datatype == "PT": #current position in time
                    if self.musicData.current_position == None or len(self.musicData.current_position) == 0:
                        output = None
                    else:
                        output = self.musicData.current_position
                        
                elif datatype == "VO": #volume
                    if self.musicData.volume == None or len(self.musicData.volume) == 0:
                        output = None
                    else:
                        output = self.musicData.volume
                        
                elif datatype == "RT": #rating
                    if self.musicData.rating == None or self.isNumeric(self.musicData.rating) == False:
                        output = None
                    else:
                        rating = int(self.musicData.rating)
                        if rating > 0:
                            output = u"".ljust(rating,ratingchar)
                        elif rating == 0:
                            output = u""
                        else:
                            output = None
                else:
                    self.logError("Unknown datatype provided: " + datatype)
                    return u""

            if output == None or self.musicData == None:
                if datatype in ["LE","PT"]:
                    output = unknown_time
                elif datatype in ["PP","VO","YR","TN"]:
                    output = unknown_number
                elif datatype == "CA":
                    output = ""                  
                else:
                    output = unknown_string
            
            if maxlength > 0 and len(output) > maxlength:
                output = output[:maxlength-3]+"..."
                
            return output
        
        except SystemExit:
            self.logError("System Exit!")
            return u""
        except Exception, e:
            traceback.print_exc()
            self.logError("Unknown error when calling getOutputData:" + e.__str__())
            return u""

    def getStatusText(self, status, statustext):
        
        if status != None:        
            statustextparts = statustext.split(",")
            
            if status == "playing":
                return statustextparts[0]
            elif status == "paused":
                return statustextparts[1]
            elif status == "stopped":
                return statustextparts[2]
            
        else:
            return status
        
    def getTemplateItemOutput(self, template_text):
        
        # keys to template data
        DATATYPE_KEY = "datatype"
        RATINGCHAR_KEY = "ratingchar"
        STATUSTEXT_KEY = "statustext"        
        NOUNKNOWNOUTPUT_KEY = "nounknownoutput"
        MAXLENGTH_KEY = "maxlength"
        
        datatype = None
        ratingchar = self.options.ratingchar #default to command line option
        statustext = self.options.statustext #default to command line option
        nounknownoutput = self.options.nounknownoutput #default to command line option
        maxlength = self.options.maxlength #default to command line option
        
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
                if key == DATATYPE_KEY:
                    datatype = value
                elif key == RATINGCHAR_KEY:
                    ratingchar = value
                elif key == STATUSTEXT_KEY:
                    statustext = value                    
                elif key == NOUNKNOWNOUTPUT_KEY:
                    nounknownoutput = True
                elif key == MAXLENGTH_KEY:
                    maxlength = int(value)
                else:
                    self.logError("Unknown template option: " + option)

            except (TypeError, ValueError):
                self.logError("Cannot convert option argument to number: " + option)
                return u""
                
        if datatype != None:
            return self.getOutputData(datatype, ratingchar, statustext, nounknownoutput, maxlength)
        else:
            self.logError("Template item does not have datatype defined")
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
    
    def writeOutput(self):

        if self.options.template != None:
            #load the file
            try:
                fileinput = codecs.open(os.path.expanduser(self.options.template), encoding='utf-8')
                template = fileinput.read()
                fileinput.close()
            except Exception, e:
                self.logError("Error loading template file: " + e.__str__())
            else:
                output = self.getOutputFromTemplate(template)
        else:
            output = self.getOutputData(self.options.datatype, self.options.ratingchar, self.options.statustext, self.options.nounknownoutput, self.options.maxlength)

        print output.encode("utf-8")

    def isNumeric(self,value):
        try:
            temp = int(value)
            return True
        except:
            return False
        
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
        print >> sys.stdout,"conkyRhythmbox v.2.07"
    else:
        if options.verbose == True:
            print >> sys.stdout, "*** INITIAL OPTIONS:"
            print >> sys.stdout, "    datatype:", options.datatype
            print >> sys.stdout, "    template:", options.template
            print >> sys.stdout, "    ratingchar:", options.ratingchar
            print >> sys.stdout, "    nounknownoutput:", options.nounknownoutput
            print >> sys.stdout, "    maxlength:", options.maxlength
            print >> sys.stdout, "    verbose:", options.verbose
            print >> sys.stdout, "    errorlogfile:",options.errorlogfile
            print >> sys.stdout, "    infologfile:",options.infologfile
            
        rhythmboxinfo = RhythmboxInfo(options)
        rhythmboxinfo.writeOutput()
    
if __name__ == '__main__':
    main()
    sys.exit()
    
