""" 
This module parsers SmarTest 7 pins-configuration files. 

This parser does not implement a lexer and parser stage becasue the 
SmarTest 7 file contains a fairly strict line-by-line syntax. This 
module mainly uses a suite of regex patterns. 

DFPT : Defines port. Resuing a port name causes the pins in the port 
       definition to be appended to the pins in the original definition.
DFGP,DFGE : Define group, group-expression. 
PSTE : Sets the number of sites. 

"""
import os, sys, re, argparse
# ----------------------------------------------------------------------------:
RE_HP93000_CONFIG = re.compile("^hp93000,config,\d\.\d$")
# TODO: Not sure what this is for, 
RE_DFPN = re.compile("^DFPN\s(?P<channelNo>[\d,]+),\"(?P<pinNo>[\w]*)\",\((?P<pinName>[\w\/]+)\)$")
# TDC: 98550 
# TODO: Technically, SmartTest7 allows for a 'connectionSet' parameter. 
# This is only supported for DC Scale PVI8, AVI64, and FVI16 cards.  
RE_DFPS = re.compile("^DFPS\s(?P<channelNo>[\d]+),(?P<polarity>[\w]+),\((?P<pinName>[\w\/]+)\)$")
RE_DFPS_GANGED = re.compile("^DFPS \((?P<channelNos>[\d,]+)\),(?P<polarity>[\w]+),\((?P<pinName>[\w\/]+)\)$")
# TDC: 98551
RE_DDCH = re.compile("^DDCH\s+(?P<dps>[\d]+),\s*(?P<channels>[\d]+)$")
# TDC: 98531
RE_RDIV = re.compile("^RDIV")
# TODO: 
# TDC: 148541
RE_PSTE = re.compile("^PSTE\s(?P<sites>[\d]+)$")
# Defines how many sites are to be configured in the pin config. 
# TDC: 98711
RE_DFUP = re.compile("^DFUP \((?P<chNoList>[\d,]+)\),\"(?P<setting>[\d]+)\",\((?P<purposeName>[\w\/]+)\)$")
# Defines a group (utility purpose) of a utility line channels and assigns a std. output state
# to each of the specified channels.
# TDC: 98559
RE_UPTI = re.compile("^UPTI (?P<time>[\d.]+),\((?P<purposeName>[\w\_\,\d ]+)\)$")
# Settling time for one or more utility purposes
# TDC: 98835
RE_CONF = re.compile("^CONF (?P<pinType>[\w]+),(?P<pinOperMode>[\w\d]+),\((?P<pinList>[\w\_\,\/]+)\)$")
# TODO: I think this regex doesnt account for 'context'. It assumes default
# TDC: 98510
RE_DFPT = re.compile("^DFPT \((?P<pinList>[\d\w\_,]+)\),\((?P<port>[\w\d\_]+)\)$")
# TDC: 98552
RE_DFGP = re.compile("^DFGP (?P<pinType>[\w]+),\((?P<pinList>[\w\d\_,\/]+)\),\((?P<pinGroup>[\w\d\_\/]+)\)$")
# TDC: 98546
RE_DFGE = re.compile("^DFGE (?P<groupType>[\w]+),\"(?P<groupExp>[\s\w\d\_,+-]+)\",\((?P<pinGroup>[\w\d\_]+)\)$")
# TDC: 98544
#RE_PSLC = re.compile("^PSLC (?P<value>[\d\.]*)[,](?P<DCSValue>[\d\.]*)),\((?P<pinList>[\d\w,_]+)\)$")
RE_PSLC = re.compile("^PSLC")
# TODO: Optional named groups
# TDC: 98700
RE_NOOP = re.compile("^NOOP (?P<param_1>\"[a-zA-Z\d\_.\s]{0,128}\"|\d*|(?!\s*)*),(?P<param_2>\"[a-zA-Z\d\_.]{0,128}\"|\d*|(?!\s*)*),(?P<param_3>\"[a-zA-Z\d\_.]{0,128}\"|\d*|(?!\s*)*),(?P<param_4>\"[a-zA-Z\d\_.]{0,128}\"|\d*|(?!\s*)*)$")
# TDC: 98664
# ----------------------------------------------------------------------------:
def read_pinconfig(sfp,debug=False):
    """ 
    This method will read the provided pinconfig file and return 
    a `Pinconfig` object. 
    """
    func = "st7p.pins.read_pinconfig"
    if debug: print("DEBUG: %s: Recieved file: %s"%(func,sfp))
    pco = Pinconfig()

    with open(sfp,"r") as fh: 
        lines = fh.readlines()
        for ln, line in enumerate(lines, start=1): 
            line = line.strip()
            #print(ln, line)
            if not line: continue 
            match = RE_HP93000_CONFIG.search(line)
            if match: continue  
            match = RE_DFPN.search(line)
            if match: 
               channelNo = match.group("channelNo")
               pinNo     = match.group("pinNo")
               pinName   = match.group("pinName")
               pco.add_dfpn(name=pinName, pogo=channelNo, pinNo=pinNo)
               continue 
            match = RE_DFPS.search(line)
            if match: 
               channels  = match.group("channelNo").split(",")
               polarity   = match.group("polarity")
               pinName    = match.group("pinName")
               pco.add_dfps(name=pinName,channels=channels,polarity=polarity)
               continue 
            match = RE_DFPS_GANGED.search(line)
            if match: 
               channels  = match.group("channelNos").split(",")
               polarity   = match.group("polarity")
               pinName    = match.group("pinName")
               pco.add_dfps(name=pinName,channels=channels,polarity=polarity)
               continue 
            match = RE_PSTE.search(line)
            if match: 
               sites   = match.group("sites")
               pco.sites = int(sites) 
               continue 
            match = RE_DFPT.search(line)
            if match: 
               pinList = match.group("pinList").split(",")
               port = match.group("port")
               pco.add_dfpt(port=port, pins=pinList)
               continue 
            match = RE_DFGP.search(line)
            if match: 
               pinType  = match.group("pinType")
               pinList  = match.group("pinList")
               pinGroup = match.group("pinGroup")
               pco.add_dfpg(family=[pinType],pins=pinList,group=pinGroup)
               continue 
            match = RE_DFGE.search(line)
            if match: 
               groupType  = match.group("groupType")
               groupExp   = match.group("groupExp")
               pinGroup   = match.group("pinGroup")
               pco.add_dfpg(family=[groupType],expr=groupExp,group=pinGroup)
               continue 
            match = RE_DFUP.search(line)
            if match: 
               chNoList = match.group("chNoList")
               setting   = match.group("setting")
               purposeName = match.group("purposeName")
               print("TODO: %s: Skipping all instances of DFUP for now."%(func))
               # TODO: 
               continue 
            match = RE_UPTI.search(line)
            if match: 
               time   = match.group("time")
               purposeName = match.group("purposeName")
               # TODO: 
               print("TODO: %s: Skipping all instances of UPTI for now."%(func))
               continue 
            match = RE_CONF.search(line)
            if match: 
               pinType   = match.group("pinType")
               pinOperMode   = match.group("pinOperMode")
               pinList = match.group("pinList")
               # TODO: 
               print("TODO: %s: Skipping all instances of CONF for now."%(func))
               continue 
            match = RE_DDCH.search(line)
            if match: 
               channels   = match.group("channels")
               dps   = match.group("dps")
               # TODO: 
               print("TODO: %s: Skipping all instances of DDCH for now."%(func))
               continue 
            match = RE_RDIV.search(line)
            if match: 
               # TODO: 
               print("TODO: %s: Skipping all instances of RDIV for now."%(func))
               continue 
            match = RE_PSLC.search(line)
            if match: 
               # TODO: 
               print("TODO: %s: Skipping all instances of PSLC for now."%(func))
               continue 
            match = RE_NOOP.search(line)
            if match: 
               # TODO: 
               print("TODO: %s: Skipping all instances of NOOP for now."%(func))
               continue 
            # other checks 
            raise RuntimeError("Couldn't handle line: %s, %s"%(ln,line))
    return pco
# ----------------------------------------------------------------------------:
class DFPN(object): 
   def __init__(self,pogo, name, pinNo=""):
       self.pogo = pogo
       self.name = name 
       self.pinNo = pinNo 
class DFPNs(object): 
    def __init__(self, ): 
        self._name_to_obj = {} 
        self._pogo_to_obj  = {}
    def add(self,name,pogo,pinNo=""): 
        if name in self._name_to_obj: 
            raise RuntimeError("Already contain defintion for DFPN %s"%(name))
        if pogo in self._pogo_to_obj: 
            raise RuntimeError("Already contain defintion for pogo %s"%(pogo))
        self._name_to_obj[name] = DFPN(name=name,pogo=pogo,pinNo=pinNo) 
        self._pogo_to_obj[pogo] = self._name_to_obj[name]
        return 
    def __len__(self): return len(self._name_to_obj)
    def length(self): 
        """Return the number of pins (DFPN) defined"""
        return len(self._name_to_obj)
# ----------------------------------------------------------------------------:
class DFPS(object): 
   def __init__(self, channels, name, polarity="", ):
       self.channels = channels
       self.name     = name 
       self.polarity = polarity
class DFPSs(object): 
    def __init__(self, ): 
        self._name_to_obj = {} 
    def add(self,name, channels, polarity): 
        if name in self._name_to_obj: 
            raise RuntimeError("Already have defintion for DFPS %s"%(name))
        self._name_to_obj[name] = DFPS(name=name,channels=channels,polarity=polarity) 
        return 
    def contains(self, name): 
        if name not in self._name_to_obj.keys(): return False 
        else: return True
    def __len__(self): return len(self._name_to_obj)
    def length(self): 
        """Return the number of power supplies (DFPS) defined"""
        return len(self._name_to_obj)
# ----------------------------------------------------------------------------:
class DFPT(object): 
   def __init__(self, port, pins):
       self.port = port
       self.pins = pins
   def extend(self, pins): 
       """Extends pins. Redundant pins are excluded."""
       for pin in pins: 
           if pin in self.pins: continue 
           else: self.pins.append(pin)
       return 
class DFPTs(object): 
    def __init__(self, ): 
        self._name_to_obj = {} 
    def add(self,port, pins): 
        if port in self._name_to_obj: self._name_to_obj[port].extend(pins)
        else: self._name_to_obj[port] = DFPT(port=port,pins=pins) 
        return 
    def contains(self, port): 
        if port not in self._name_to_obj.keys(): return False 
        else: return True
    def __len__(self): return len(self._name_to_obj)
    def length(self): 
        """Return the number of port (DFPT) defined"""
        return len(self._name_to_obj)
# ----------------------------------------------------------------------------:
# TODO: Expand expression
class DFPG(object): 
   def __init__(self, family, pins, group, expr=False):
       self.family = family
       self.pins = pins 
       self.group = group 
       self.expr = expr
   def extend(self, family, pins): 
       """Extends pins. Redundant pins are excluded."""
       self.family.append(family)
       for pin in pins: 
           if pin in self.pins: continue 
           else: self.pins.append(pin)
       return 
class DFPGs(object): 
    def __init__(self, ): 
        self._name_to_obj = {} 
    def add(self,family, group, pins ="", expr=""): 
        if not pins and not expr:
            raise ValueError("Must provide either pins or expr.")
        if expr: pins = [expr] # TODO: need utility to unpack. Could wait till runtime
        if group in self._name_to_obj: self._name_to_obj[group].extend(family,pins)
        else: self._name_to_obj[group] = DFPG(family=family,pins=pins,group=group) 
        if expr: self._name_to_obj[group].expr = True
        return 
    def contains(self, group): 
        if port not in self._name_to_obj.keys(): return False 
        else: return True
    def __len__(self): return len(self._name_to_obj)
    def length(self): 
        """Return the number of groups (DFPG) defined"""
        return len(self._name_to_obj)
    def groups(self,): 
        """Return the list of all group names."""
        return self._name_to_obj.keys()
# ----------------------------------------------------------------------------:
# NOTE: We have decouple the 'reading' and the Pinconfig object. 
# the reason for this is becasue I want the ability to read and
# write pin-config files. Thus, we need to separate them. 
class Pinconfig(object): 
    def __init__(self, sfp="", debug=False):
        self._sfp = sfp 
        self._debug = debug 
        self.pins     = DFPNs() 
        self.supplies = DFPSs()
        self.ports    = DFPTs()
        self.groups   = DFPGs()
        self.sites    = 0 # Set by PSTE
    def add_dfpn(self,name,pogo,pinNo): 
        self.pins.add(name=name,pogo=pogo,pinNo=pinNo)
    def add_dfps(self,channels,name,polarity): 
        self.supplies.add(channels=channels,name=name,polarity=polarity)
    def add_dfpt(self,port,pins): 
        self.ports.add(port=port, pins=pins)
    def add_dfpg(self,family,group,pins="",expr=""): 
        """Handles both DFPG and DFGE.""" 
        self.groups.add(family=family,pins=pins,expr=expr,group=group)
# ----------------------------------------------------------------------------:
def __handle_cmdline_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", 
                        help="Increase console logging", 
                        action="store_true")
    parser.add_argument("pinconfig", help="Pin-config file path")
    args = parser.parse_args()
    if not os.path.isfile(args.pinconfig): 
        raise ValueError("Invalid pin-config file")
    return args
# ----------------------------------------------------------------------------:
if __name__ == "__main__": 
    args = __handle_cmdline_args()
    if args.debug: 
        print("DEBUG: Main st7p.pins module")
    pco = read_pinconfig(sfp = args.pinconfig, debug = args.debug)
    print("\nNOTE: If in interactive mode, use variable name 'pco' to"\
          " the parsed Pinconfig object.")


