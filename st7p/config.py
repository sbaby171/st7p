""" 
This module parsers SmarTest 7 pins-configuration files. 

This parser does not implement a lexer and parser stage becasue the 
SmarTest 7 file contains a fairly strict line-by-line syntax. This 
module mainly uses a suite of regex patterns. 

Note to self: because the configuration file is variable fields for a
given command, its line-by-line, we can probably get away with simply 
checking the front of the line. 

"""
import os, sys, re, argparse
from collections import OrderedDict
import st7putils 
# ----------------------------------------------------------------------------:
def dut_interface(): 
    x = """
The V9300 test head can be configured with different combinations of different
types of cards to meet specific test requirements. 


 ===============================================================================================
|   ___________________    ___________________    ___________________    ___________________     |
|  |      Group 7      |  |      Group 8      |  |      Group 2      |  |      Group 6      |    |
|  |-------------------|  |-------------------|  |-------------------|  |-------------------| 
|  | DPS.7 |  | UTIL.8 |  | DPS.8 |  | UTIL.4 |  | DPS.2 |  | UTIL.3 |  | DPS.6 |  | UTIL.7 |     |
|  | (272) |  | (172)  |  | (268) |  | (168)  |  | (267) |  | (167)  |  | (271) |  | (171)  | 
|  | -424- |  | -420-  |  | -432- |  | -428-  |  | -316- |  | -312-  |  | -416- |  | -412-  | 
 






|  | 224   | | 220   |    | 224   | | 220   |    | 224   | | 220   |    | 224   | | 220   |     |
|  | 223   | | 219   |    | 224   | | 220   |    | 224   | | 220   |    | 224   | | 220   |     |
|  | 222   | | 218   |    | 222   | | 218   |    | 222   | | 218   |    | 222   | | 218   |     |
|  | 221   | | 217   |    | 222   | | 218   |    | 222   | | 218   |    | 222   | | 218   |     |
|   ^^^^^^^   ^^^^^^^      ^^^^^^^   ^^^^^^^      ^^^^^^^   ^^^^^^^      ^^^^^^^   ^^^^^^^      |
|                                                                                               |
|   _______   _______      _______   _______      _______   _______      _______   _______      |
|  | DPS 7 | | Util.8|    | DPS 8 | | Util.4|    | DPS 7 | | Util.8|   || DPS 7 | | Util.8||    |
|  | 224   | | 220   |    | 224   | | 220   |    | 224   | | 220   |   || 224   | | 220   ||    |
|  | 223   | | 219   |    | 224   | | 220   |    | 224   | | 220   |   || 224   | | 220   ||    |
|  | 222   | | 218   |    | 222   | | 218   |    | 222   | | 218   |   || 222   | | 218   ||    |
|  | 221   | | 217   |    | 222   | | 218   |    | 222   | | 218   |   || 222   | | 218   ||    |
|   ^^^^^^^   ^^^^^^^      ^^^^^^^   ^^^^^^^      ^^^^^^^   ^^^^^^^    | ^^^^^^^   ^^^^^^^ |    | 
| |      Group 7      |  |      Group 8      |  |      Group 2      |  |      Group 6      |    |
|  ^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^     |
 ===============================================================================================
    """
    print(x)
    return 

# ----------------------------------------------------------------------------:
# 




# DFDM: Missing from TDC.
# The only entry is on TDC topic 150673, "Enabling upgrade licenses using the 
# DC Scale Extensions editor" 
# 
# 'Data that are defined by the DC Scale Extensions Editor are stored in 
# the pin configuration file using the FW command DFDM'


RE_HP93000_CONFIG = re.compile("^hp93000,config,\d\.\d$")
RE_DDCH = re.compile("^DDCH\s+(?P<dps>[\d]+),\s*(?P<channels>[\d]+)$") 
RE_PSTE = re.compile("^PSTE\s(?P<sites>[\d]+)$")
RE_NOOP = re.compile("^NOOP (?P<param_1>\"[a-zA-Z\d\_.\s]{0,128}\"|\d*|(?!\s*)*),(?P<param_2>\"[a-zA-Z\d\_.]{0,128}\"|\d*|(?!\s*)*),(?P<param_3>\"[a-zA-Z\d\_.]{0,128}\"|\d*|(?!\s*)*),(?P<param_4>\"[a-zA-Z\d\_.]{0,128}\"|\d*|(?!\s*)*)$")
# TDC: 98664
RE_DDIC = re.compile("^DDIC ")
# TODO:
RE_PSSL = re.compile("^PSSL\s+(?P<minV>[OFF0-9\.]+)\s*,\s*(?P<maxV>[OFF0-9\.]+)\s*,\s*(?P<maxSourceI>[OFF0-9\.]+)\s*,\s*(?P<maxSinkI>[OFF0-9\.]+)\s*,\s*\((?P<pins>.*)\)")
# TODO: Power Supply Safety Limits TDC: 143177

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
RE_PALS_NO_CHN3 = re.compile("PALS\s*(?P<site>\d+)\s*,\s*(?P<chns1>[\d,\(\)]+)\s*,\s*(?P<chns>[\d,]*)\s*,\s*\((?P<name>[\w\/]+)\)")
# TODO: Channel 3 is typically for FVI16 HW

RE_UPAS = re.compile("UPAS\s+(?P<site>\d+)\s*,\s*\"(?P<data>[01Xx]+)\"\s*,\s*\((?P<name>[\w\/]+)\)")


RE_DFPN_TYP = re.compile("^DFPN\s+(?P<channelNo>\d+)\s*,\s*\"(?P<pinNo>[\w\s]*)\"\s*,\s*\((?P<pinName>[\w\/\[\]]+)\)$")
RE_DFPN_GNG = re.compile("^DFPN\s+\((?P<channelNo>[\d\,\s]+)\),\"(?P<pinNo>[\w\s]*)\",\((?P<pinName>[\w\/]+)\)$")

RE_DFPS_SNG_CHN = re.compile("^DFPS\s*(?P<chn>\d+),(?P<polarity>[\w]+),\((?P<name>[\w\/]+)\)$")
RE_DFPS_GNG_RNG = re.compile("^DFPS\s*\((?P<start>\d+)\-(?P<end>\d+)\),(?P<polarity>[\w]+),\((?P<name>[\w\/]+)\)$")
RE_DFPS_GNG_LST = re.compile("^DFPS\s*\((?P<chns>[\d,]+)\),(?P<polarity>[\w]+),\((?P<name>[\w\/]+)\)$") 

RE_DFGP = re.compile("^DFGP (?P<pinType>[\w]+),\s*\((?P<pinList>[\w,\/\s\[\]]+)\),\((?P<pinGroup>[\w\d\_\/]+)\)$")
RE_DFGE = re.compile("^DFGE (?P<groupType>[\w]+),\"(?P<groupExp>[\s\w\d\+\-\*]+)\",\((?P<pinGroup>[\w\d\_]+)\)$")

RE_CONF_CTX = re.compile("^CONF \"(?P<ctx>\w+)\"\s*,\s*(?P<pinType>[\w]+),(?P<pinOperMode>[\w\d]+),\((?P<pinList>[\w,\/\[\]]+)\)$")
RE_CONF_REG = re.compile("^CONF (?P<pinType>[\w]+),(?P<pinOperMode>[\w\d]+),\((?P<pinList>[\w,\/\[\]]+)\)$")

RE_DFPT = re.compile("^DFPT\s*\((?P<pinList>[\w\,\s\@\[\]]+)\),\s*\((?P<port>[\w]+)\)$")

RE_DFUP = re.compile("^DFUP \((?P<chNoList>[\d\s,]+)\)\s*,\s*\"(?P<setting>[01xX]+)\"\s*,\s*\((?P<name>[\w\/]+)\)$")
RE_UPTI = re.compile("^UPTI (?P<time>[\d\.]+),\((?P<name>[\w\,]+)\)$")

RE_RDIV = re.compile("^RDIV\s+(?P<val>[\d\.]+),\((?P<pinlist>[\w,\@]+)\)")  
RE_PSLC = re.compile("^PSLC\s+(?P<val>[\d\.]+),\((?P<pinlist>[\w,\@]+)\)")  



GRP_PIN_TYPES = ["I","O","IO","DC","X"]

CONF_PIN_TYPES = ['I','O','IO','DC','OFF']
# The PIN_TYPES list is to contains all the allowed pin-types as 
# defined within the CONF command. 
CONF_PIN_OP_MODES = ['DCSIGNAL','POWER','F160','F330','FAST','HV','STDDIFF','FASTDIFF']
# ^^^ this contains all the allowed pin-oper-modes as 
# defined within the CONF command. 


# ----------------------------------------------------------------------------:
def read(sfp,debug=False):
    """ 
    This method will read the provided pinconfig file and return 
    the parsed object. 
    """
    func = "st7p.pins.read"
    if debug: print("DEBUG: %s: Recieved file: %s"%(func,sfp))
    obj = Config(sfp=sfp)
    with open(sfp,"r") as fh: 
        lines = fh.readlines()
        for ln, line in enumerate(lines, start=1): 
            line = line.strip()
            if debug: print("DEBUG: (%s): [%d] %s"%(func,ln,line))
            #print("DEBUG: (%s): [%d] %s"%(func,ln,line))
            if not line: continue 
            match = RE_HP93000_CONFIG.search(line)
            if match: continue  

            if line.startswith("DFPN"): obj.pins.add(Pins.process_dfpn(line,debug=debug));continue 
            if line.startswith("DFPS"): obj.supplies.add(Supplies.process_dfps(line,debug=debug));continue 
            if line.startswith("DFGP"): obj.groups.add(Groups.process_dfgp(line,debug=debug));continue
            if line.startswith("DFGE"): obj.groups.add(Groups.process_dfge(line,cfo=obj,debug=debug));continue
            if line.startswith("DFUP"): obj.utility_purposes.add(UtilityPurposes.process_dfup(line,debug=debug));continue
            if line.startswith("PSTE"): obj.sites = int(line[4:].strip()); continue 
            if line.startswith("PALS"): obj._process_pals(line,debug=debug); continue 
            if line.startswith("UPAS"): obj._process_upas(line,debug=debug); continue 

            if line.startswith("DFPT"): 
                pinlist, name = RE_DFPT.search(line).groups()
                obj.ports.add(Port(name,[x.strip() for x in pinlist.split(",")]))
                continue 

            if line.startswith("UPTI"): 
                time, names = RE_UPTI.search(line).groups()
                for name in names.split(","): 
                    obj.utility_purposes[name.strip()].settling_time = time
                continue 

            if line.startswith("CONF"): 
                ctx = RE_CONF_CTX.search(line)
                cnf = RE_CONF_REG.search(line)
                if   ctx: context,pintype,pin_op_mode,pinlist = ctx.groups() 
                elif cnf: context = "DEFAULT"; pintype,pin_op_mode,pinlist = cnf.groups()
                else: raise RuntimeError("Bad CONF cmd: %s"%(line))
                if pintype == "DC": 
                    for supply in pinlist.split(","):
                        pin = pin.strip()
                        obj.supplies[supply].context = context
                        obj.supplies[supply].pin_type = pintype
                        obj.supplies[supply].pin_op_mode = pin_op_mode
                    continue 
                elif pintype in ["IO","I","O"]: 
                    for pin in pinlist.split(","): 
                        pin = pin.strip()
                        obj.pins[pin].context  = context
                        obj.pins[pin].pin_type = pintype
                        obj.pins[pin].pin_op_mode= pin_op_mode
                    continue 
                raise RuntimeError("CONF pintype (%s) not supported"%(pintype))

            match = RE_RDIV.search(line)
            if match: 
                val, pinlist = match.groups()
                if    pinlist =="@": pinlist = obj.pins.names()
                else: pinlist = pinlist.split(',')
                for pin in pinlist: obj.pins[pin.strip()].rdiv = float(val)
                continue 
            match = RE_PSLC.search(line)
            if match: 
                val, pinlist = match.groups()
                if    pinlist =="@": pinlist = obj.supplies.names()
                else: pinlist = pinlist.split(',')
                for supply in pinlist: obj.supplies[supply.strip()].load_cap = float(val)
                continue 

            if line.startswith("NOOP"): 
                if debug: print("DEBUG: (%s): Skipping instances of 'NOOP'"%(func))
                continue 

            # ================================================================: 
            # RECENT UPDATES =================================================: 
            if line.startswith("PSSL"): 
                match = RE_PSSL.search(line) 
                if not match: raise RuntimeError("problem with PSSL line: [%s] %s"%(ln,line))
                minV, maxV, maxSourceI, maxSinkI, pinlist = match.groups()
                for pin in pinlist.split(","): 
                    pin = pin.strip()
                    obj.supplies[pin].minV = minV
                    obj.supplies[pin].maxV = maxV
                    obj.supplies[pin].maxSourceI = maxSourceI
                    obj.supplies[pin].maxSinkI = maxSinkI
                continue 
            # TODO Section ---------------------------------------------------:
            if line.startswith("UDEF"): print("TODO: %s: Skipping instances of UDEF: %s"%(func,line));continue  # TODO: 
            if line.startswith("DFAN"): print("TODO: %s: Skipping instances of DFAN: %s"%(func,line));continue  # TODO: 
            if line.startswith("UDAN"): print("TODO: %s: Skipping instances of UDAN: %s"%(func,line));continue  # TODO: 
            if line.startswith("UDPS"): print("TODO: %s: Skipping instances of UDPS: %s"%(func,line));continue  # TODO: 
            if line.startswith("DFUT"): print("TODO: %s: Skipping instances of DFUT: %s"%(func,line));continue  # TODO: 
            if line.startswith("UDUT"): print("TODO: %s: Skipping instances of UDUT: %s"%(func,line));continue  # TODO: 
            if line.startswith("UDUP"): print("TODO: %s: Skipping instances of UDUP: %s"%(func,line));continue  # TODO: 
            #if line.startswith("UPAS"): print("TODO: %s: Skipping instances of UPAS: %s"%(func,line));continue  # TODO: 
            if line.startswith("DFPR"): print("TODO: %s: Skipping instances of DFPR: %s"%(func,line));continue  # TODO: 
            if line.startswith("UDPR"): print("TODO: %s: Skipping instances of UDPR: %s"%(func,line));continue  # TODO: 
            if line.startswith("PACT"): print("TODO: %s: Skipping instances of PACT: %s"%(func,line));continue  # TODO: 
            #if line.startswith("PALS"): print("TODO: %s: Skipping instances of PALS: %s"%(func,line));continue  # TODO: 
            if line.startswith("PQFC"): print("TODO: %s: Skipping instances of PQFC: %s"%(func,line));continue  # TODO: 
            if line.startswith("PSFC"): print("TODO: %s: Skipping instances of PSFC: %s"%(func,line));continue  # TODO: 
            if line.startswith("STME"): print("TODO: %s: Skipping instances of STME: %s"%(func,line));continue  # TODO: 
            if line.startswith("DDCH"): print("TODO: %s: Skipping instances of DDCH: %s"%(func,line));continue  # TODO: 
            if line.startswith("DDIC"): print("TODO: %s: Skipping instances of DDIC: %s"%(func,line));continue  # TODO
            if line.startswith("PSVR"): print("TODO: %s: Skipping instances of PSVR: %s"%(func,line));continue  # TODO
            if line.startswith("DDSL"): print("TODO: %s: Skipping instances of DDSL: %s"%(func,line));continue  # TODO
            if line.startswith("PSLC"): print("TODO: %s: Skipping instances of PSLC: %s"%(func,line));continue  # TODO
            if line.startswith("DFDM"): print("TODO: %s: Skipping instances of DFDM: %s"%(func,line));continue  # TODO
            if line.startswith("PSRG"): print("TODO: %s: Skipping instances of PSRG: %s"%(func,line));continue  # TODO
            if line.startswith("PSVD"): print("TODO: %s: Skipping instances of PSVD: %s"%(func,line));continue  # TODO
            if line.startswith("PSSF"): print("TODO: %s: Skipping instances of PSSF: %s"%(func,line));continue  # TODO
            if line.startswith("noop"): print("TODO: %s: Skipping instances of noop: %s"%(func,line));continue
            raise RuntimeError("Couldn't handle line: %s, %s"%(ln,line))
    ## Add '@' port
    obj.ports.add(Port("@",pins=obj.pins.names()))
    return obj




# ----------------------------------------------------------------------------:
class Pin(object): 
   def __init__(self,channels,name,site=1,pinNo="",rdiv=0.0):
       self.channels = {site:channels}
       self.name     = name 
       self.pinNo    = pinNo 
       self.context  = "DEFAULT" # defined w/in the CONF
       self.pin_type = "" # defined w/in the CONF
       self.pin_op_mode = "" # defined w/in the CONF
       self.rdiv  = rdiv # Resistive Divider 

   def __str__(self,): 
       return str(self.__dict__)

class Pins(st7putils.Container): 
    def __init__(self, ): 
        super(Pins,self).__init__()
    def add(self,pin): 
        super(Pins,self).add(pin,Pin)

    @staticmethod
    def process_dfpn(dfpn,debug=False):
        func = "Pins.process_dfpn"
        if not dfpn.startswith("DFPN"): raise RuntimeError("input must start with 'DFPN'")
        fc = dfpn[4:].strip()[0]
        ## Check first char: it defines connectionSet, digital channel, or DC Scale ganging. 
        if fc == "\"": 
            print("%s: connectionSet due to first char '\"'"%(func))
            raise RuntimeError("According to 7.10 documentation, this option is not supported.")
        elif fc == "(": 
            print("%s: DC Scale Ganging due to first char '('"%(func))
            match = RE_DFPN_GNG.search(dfpn)
            if not match: raise RuntimeError("Bad DFPN syntax: %s"%(dfpn))
            channels = [channel.strip() for channel in match.group("channelNo").split()]
            pin = Pin(name=match.group("pinName"), channels=channels, pinNo=match.group("pinNo").strip())
        elif fc.isdigit(): 
            #print("%s: channel num due to first char a digit"%(func))
            match = RE_DFPN_TYP.search(dfpn)
            if not match: raise RuntimeError("Bad DFPN syntax: %s"%(dfpn))
            pin = Pin(name=match.group("pinName"), channels=[match.group("channelNo")], pinNo=match.group("pinNo").strip())
        else: raise RuntimeError("Bad first char of dfpn: %s"%(dfpn[0]))

        return pin
# ----------------------------------------------------------------------------:

# ----------------------------------------------------------------------------:
class Supply(object): 
   def __init__(self, name, channels, site = 1, polarity="", load_cap = 0.0):
       #self.channels    = channels # This needs to be site specific
       try: site = int(site)
       except: raise RuntimeError("Site must be an integer")
       self.channels = {site:channels}
       self.name        = name 
       self.polarity    = polarity
       self.load_cap = load_cap  # TODO: Need diff name? Set via PSLC (power supply load capacitance) 
       self.context  = "DEFAULT" # defined w/in the CONF
       self.minV = "OFF"         # Set via PSSL(power supply safety limits) command 
       self.maxV = "OFF"         # Set via PSSL(power supply safety limits) command 
       self.maxSourceI = "OFF"   # Set via PSSL(power supply safety limits) command 
       self.maxSinkI = "OFF"     # Set via PSSL(power supply safety limits) command 
       self.pin_type = ""        # defined w/in the CONF
       self.pin_op_mode = ""     # defined w/in the CONF

   def is_ganged(self,site=1): 
       """Site-specific. If no site is provide, site-1 is assumed."""
       if self.channels[site].__len__() >= 2: return True
       else: return False  

   def __str__(self): 
       return "SUPPLY: %s, %s, %s"%(self.name,self.polarity,self.channels)

   def report(self): 
       retstr = ["%-16s, %s\n"%(self.name,self.polarity)]
       retstr.append("  - \n")

class Supplies(st7putils.Container): 
    def __init__(self, ): 
        super(Supplies,self).__init__()
        self._gangedMapping = None 

    def add(self,supply): 
        super(Supplies,self).add(supply,Supply)

    def report(self):
        for i,supplyName in enumerate(self.objects,start=1): 
            print(i,self.objects[supplyName].__str__())


    def get_ganged_map(self, descending=True): 
        """
        Returns a mapping of ganged supplies in descending order.

        Parameters: 
          descending : True, Boolean 
            If False, the dictionary is return in ascending order.
        """
        if self._gangedMapping: return self._gangedMapping 
        self._gangedMapping = OrderedDict()
        for supply in self.objects: 
            supply = self.objects[supply]
            if supply.is_ganged(): 
               self._gangedMapping[supply.name] = supply.channels.__len__()
        self._gangedMapping = OrderedDict(sorted(self._gangedMapping.iteritems(), key=lambda x: x[1], reverse=True)) 
        return self._gangedMapping

    @staticmethod
    def process_dfps(dfps,debug=False):
        """The goal is to parse a DFPS line and create an instance 
        of the Supply class. """
        func = "Supplies.process_dfps"
        if not dfps.startswith("DFPS"): raise RuntimeError("input must start with 'DFPS'")
        fc = dfps[4:].strip()[0]
        if fc == "(": 
            #print("%s: DC Scale Ganging due to first char '('"%(func))
            match = RE_DFPS_GNG_RNG.search(dfps)
            if match: 
                start, end, polarity, name = match.groups()
                channels = range(start,end+1)
                return Supply(name=name,channels=channels,polarity=polarity)
            match = RE_DFPS_GNG_LST.search(dfps)
            if match: 
                channels, polarity, name = match.groups()
                channels = channels.split(",")
                return Supply(name=name,channels=channels,polarity=polarity) 
            raise RuntimeError("Received bad DPS ganging cmd: %s"%(dfps))
        elif fc.isdigit(): 
            match = RE_DFPS_SNG_CHN.search(dfps)
            if not match: raise RuntimeError("Bad DFPS syntax: %s"%(dfps))
            return Supply(name=match.group("name"),channels=[match.group("chn")],polarity=match.group("polarity"))
        raise RuntimeError("Bad DFPS syntax: %s"%(dfps))
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
class Port(object): 
   def __init__(self, name, pins):
       self.name = name
       self.pins = pins

   def extend(self, pins): # TODO: Is this needed ? 
       """Extends pins. Redundant pins are excluded."""
       for pin in pins: 
           if pin in self.pins: continue 
           else: self.pins.append(pin)
       return 

   def __len__(self): 
       return len(self.pins)

   def length(self): 
       return len(self.pins)

   def __str__(self,): 
       return "PORT: %s, %s"%(self.name,self.pins)
   

class Ports(st7putils.Container): 
    def __init__(self, ): 
        super(Ports,self).__init__()

        self._portLengthMapping = None

    def add(self,port): 
        super(Ports,self).add(port,Port)


    def port_length_mapping(self, descending=True): 
        """Returns the port name to port length mapping.

        Parameters: 
          descending : True, Boolean 
            If False, the dictionary is return in ascending order.
        """
        # if not self._portLengthMapping: return self._portLengthMapping
        # ^^^ TODO: This was removed because we want to be able to update the 
        # mapping at runtime. This can handle via a parameter (e.g. update = False)
        self._portLengthMapping = OrderedDict()
        for port in self.objects: 
            self._portLengthMapping[port] = self.objects[port].length()
        self._portLengthMapping = OrderedDict(sorted(self._portLengthMapping.iteritems(), key=lambda x: x[1], reverse=descending)) 
        return self._portLengthMapping
         


  
        

# ----------------------------------------------------------------------------:
# TODO: Expand expression
class Group(object): 
   def __init__(self, name, pin_type, pins, expr=False):
       self.name = name 
       self.expr = expr
       #  ^^^ TODO: How should we extract the pins for expr. I think we should 
       # probably do it at DFGE
       if pin_type not in GRP_PIN_TYPES: 
           raise RuntimeError("Pin type '%s' is not supported")
       self.pin_types = {}
       for pin in pins: 
           self.pin_types[pin] = [pin_type]
       self.pins = pins  
       # ^^^ NOTE:  There really is no need to store this. It could simply be 
       # be a function return return of th keys of pin_types. but that would be
       # inconsistent with other forms.
       

   def extend(self, pin_type, pins): 
       """Extends pins. Redundant pins are excluded."""
       if pin_type not in GRP_PIN_TYPES: 
           raise RuntimeError("Pin type '%s' is not supported")
       for pin in pins: 
           if pin in self.pins: continue 
           self.pins.append(pin)
           self.pin_types[pin].append(pin_type)
       return 

# TODO: Need to Finish 
class Groups(st7putils.Container):  
    def __init__(self, ): 
        super(Groups,self).__init__()

    def add(self,group): 
        if not isinstance(group,Group): 
            raise ValueError("Must provide instance of %s"%(Group))
        if group.name in self.objects: # Group has already been allocated
            #if group.pin_type != self.objects[group.name].pin_type:  
            #    self.objects[group.name].pin_type += group.pin_type
            #    # TODO: Below is a check on the pin types. Turns out pins within a group can be configed diff. 
            #    #if set(group.pins) != set(self.objects[group.name].pins): 
            #    #    print(set(group.pins))
            #    #    print(set(self.objects[group.name].pins))
            #    #    raise RuntimeError("Updating group pin-type '%s.%s' but pinlists dont match."%(group.name,group.pin_type))
            for pin,pin_type in group.pin_types.items(): 
                if pin in self.objects[group.name].pins: 
                   if pin_type in self.objects[group.name].pin_types[pin]: 
                       continue 
                   else: self.objects[group.name].pin_types[pin].append(pin_type)
                else: 
                   self.objects[group.name].pins.append(pin)
                   self.objects[group.name].pin_types[pin] =[ pin_type ]
                
        else: super(Groups,self).add(group,Group)

    @staticmethod
    def process_dfgp(line,debug=False):
        func = "Groups.process_dfgp"
        match = RE_DFGP.search(line)
        if not match: raise RuntimeError("Bad 'DFGP' line: %s"%(line))
        pt, pl, gn = match.groups()
        if pt not in GRP_PIN_TYPES: raise RuntimeError("Bad group pin type: %s"%(pt))
        pl = [p.strip() for p in pl.split(",")]
        return Group(name=gn.strip(),pin_type=pt,pins=pl,expr=False)

    @staticmethod
    def process_dfge(line,cfo=None,debug=False):
        func = "Groups.process_dfge"
        match = RE_DFGE.search(line)
        if not match: raise RuntimeError("Bad 'DFGE' line: %s"%(line))
        pt, pe, gn = match.groups()
        if pt == "X": raise RuntimeError("Pin type 'X' is not allowed for DFGE")
        if pt not in GRP_PIN_TYPES: raise RuntimeError("Bad group pin type: %s"%(pt))
        if not cfo: 
            print("WARNING: (%s): No Config object provided. Just storing expr as pins for DFGE."%(func))
            return Group(name=gn.strip(),pin_type=pt,pins=pe,expr=True)

        else: 
            pins_dict = OrderedDict()
            queue = [ ]
            flag = "+"
            for char in pe:  
                if char == '': continue  
                if re.search("\w|\/",char): queue.append(char); continue 
                if char == "+" or char == "-":  
                    pins_dict["".join(queue)] = flag; queue = []; flag = char; continue 
            pins_dict["".join(queue)] = flag; queue = []; flag = char 
    
            pins = set()
            for item, flag in pins_dict.items(): 
                if item in cfo.pins.names(): 
                    if flag == "+": pins.add(item)
                    elif flag == "-": pins.remove(item)
                    else: raise RuntimeError("Unsupported flag type: %s"%(flag))
                elif item in cfo.groups.names():  
                    _pins = cfo.groups[item].pins 
                    if flag == "+": 
                        for _pin in _pins: pins.add(_pin)
                    if flag == "-":
                        for _pin in _pins: 
                            if _pin in pins: pins.remove(_pin)
                            else: pass 
                else: raise RuntimeError("Pin item %s in not a Pin or Group"%(item))
            return Group(name=gn.strip(),pin_type=pt,pins=list(pins),expr=True)
   
                    
  
        
        # TODO: Create kernal to parse the expression and use the obj.groups 
        # to build the actuall pin list. 
        # Thus `pins` get properly set, then we pass the expr so that it is stored.
        



# ----------------------------------------------------------------------------:
class UtilityPurpose(object): 
    def __init__(self, name, channel_settings = {}, settling_time=0):
        """ 
        channel_settings : dictionary of dictionary 
          [site] -> {'<channel>':'<data>'}
        """
        self.name = name 
        self.channel_settings = channel_settings # TODO this needs to be done per site
        self.settling_time = settling_time # Note, units ms. 

    def channels(self): 
        return self.channel_settings.keys()

    def length(self): 
        return len(self.channel_settings)
   
    def __len__(self): 
        return len(self.channel_settings)
 
    def __getitem__(self, channel): 
        return self.channel_settings[channel]

    def __iter__(self): 
        for channel in self.channel_settings.keys(): 
            yield self.channel_settings[channel]

    def items(self): 
        return self.channel_settings.items()

    def __str__(self): 

        sites = self.channel_settings.__len__()
        #for site in range(1,sites+1): 
        #    print(site)
        #return ""

        retstr = [self.name]
        for site, up in self.channel_settings.items():
            for chn,val in up.items(): 
                retstr.append("site: %s -> (chn = %s, val = %s)"%(site,chn,val)) 
        return "\n".join(retstr)
    


class UtilityPurposes(st7putils.Container):  
    def __init__(self, ): 
        super(UtilityPurposes,self).__init__()

    def add(self,ut): 
        super(UtilityPurposes,self).add(ut,UtilityPurpose)

    @staticmethod
    def process_dfup(line,debug=False):
        func = "UtilityPurposes.process_dfup"
        match = RE_DFUP.search(line)
        if not match: raise RuntimeError("Bad 'DFUP' line: %s"%(line))
        chns, settings, name = match.groups()
        chns = [chn.strip() for chn in chns.split(",")]
        settings = list(settings)
        if len(chns) != len(settings): 
            print("ERROR: (%s): len(%s) != len(%s)"%(func,len(chns),len(settings)))
            raise RuntimeError("Utility Purpose channels and settings length dont match: %s"%(line))
        chn_settings = {1:OrderedDict(zip(chns,settings))}
        return UtilityPurpose(name=name.strip(),channel_settings = chn_settings)

        


# ----------------------------------------------------------------------------:
# NOTE: We have decouple the 'reading' and the Pinconfig object. 
# the reason for this is becasue I want the ability to read and
# write pin-config files. Thus, we need to separate them. 

class Config(object): 
    def __init__(self, sfp="", debug=False):
        if sfp:  self._abs_path, self._dd_path, self._filename = st7putils._93k_file_handler(sfp, "configuration")
        else:    self._abs_path = ""; self._dd_path = ""; self._filename = ""; 
        self._debug = debug 
        self.pins      = Pins() 
        self.supplies  = Supplies()
        self.ports     = Ports()
        self.groups    = Groups()
        self.utility_purposes = UtilityPurposes() 
        self.sites     = 0 # Set by PSTE



    def _process_upas(self,line,debug=False): 
        func = "Config._process_upas"
        if not line.startswith("UPAS"): raise RuntimeError("input must start with 'UPAS'")
        # RE_UPAS = re.compile("UPAS\s+(?P<site>\d+)\s*,\s*\"(?P<data>[01X]+)\"\s*,\s*\((?P<name>[\w\/]+)\)")
        match = RE_UPAS.search(line)
        if match: 
            site, data, name = match.groups(); site = int(site);
            channels_list = list(self.utility_purposes[name].channel_settings[1].keys())
            data_list = data.split
            #print(channels_list)
            channel_settings = OrderedDict()
            i = 0
            for channel in channels_list: 
                channel_settings[channel] = data[i] 
                i += 1
            self.utility_purposes[name].channel_settings[site] = channel_settings 
            #sys.exit(1) 
        else: raise RuntimeError("UPAS line bad format: %s"%(line))



    def _process_pals(self,line,debug=False): 
        func = "Config._process_pals"
        if not line.startswith("PALS"): raise RuntimeError("input must start with 'PALS'")
        # RE_PALS_NO_CHN3 = re.compile("PALS\s+(?P<site>\d+)\s*,\s*(?P<chns1>[\d,]+),(?P<chns2>[\d,]*)\s*,\s*\((?P<name>[\w\/]+)\)")
        match = RE_PALS_NO_CHN3.search(line)
        if match: 
            site, chns1, chns2, name = match.groups(); site = int(site);
            print(site,chns1,chns2,name)
            if name in self.pins: 
                #if site in self.pins[pin].channels: raise RuntimeError("Site is already configured for %s"%(name))
                if len(chns1.split(",")) > 1: raise RuntimeError("Not expecting ganged channels on digital pin (this might be fro DC Scale channel). %s"%(line)) 
                if chns1.startswith("("): raise RuntimeError("Not expecting ganged channels on digital pin (this might be fro DC Scale channel). %s"%(line)) 
                self.pins[name].channels[site] = [chns1]
                # Sanity checks: 
                if chns2 != "": raise RuntimeError("Expecting empty chns2 slot for Digital pin entry: %s"%(line))
                print("DEBUG: (%s): Added site %s channels %s to pin %s"%(func,site,chns1,name))

            if name in self.supplies: 
                if len(chns1.split(",")) > 1: 
                    if not chns1.startswith("("): 
                        raise RuntimeError("PALS syntax for ganged supply is not correct. %s"%(line)) 
                    chns1 = [x.strip(" ()") for x in chns1.split(',')]
                else: chns1 = [chns1]
                self.supplies[name].channels[site] = chns1
                if chns2 != "": raise RuntimeError("Expecting empty chns2 slot for DPS pin entry (unless DC Scale): %s"%(line))
                print("DEBUG: (%s): Added site %s channels %s to supply %s"%(func,site,chns1,name))
        else: raise RuntimeError("PALS line cannot be processed: %s"%(line))
        
        

    #def add_dfpn(self,name,pogo,pinNo): 
    #    self.pins.add(Pin(name=name,pogo=pogo,pinNo=pinNo))
    def add_dfps(self,pogos,name,polarity): 
        self.supplies.add(Supply(pogos=pogos,name=name,polarity=polarity))
    def add_dfpt(self,name,pins): 
        self.ports.add(Port(name=name, pins=pins))
    def add_dfpg(self,pin_type,name,pins="",expr=""): # TODO: Need to refactor
        """Handles both DFPG and DFGE.""" 
        self.groups.add(pin_type=pin_type,pins=pins,expr=expr,name=name)


    def get_pins_from_ports(self,ports,no_duplicates = False): 
        """
        This function will return all the pins defined within the provided
        ports. 

        Background: this came from development of st7p.timing.eqnset_compare.
        We need a way to aquire th e pin list from the DEFINES keyword. 
 
        Parameters: 
            ports : list-of-strings
              list of port names we wish to qcquire pin list.

            no_duplicates: Boolean (optional: defaul -> False)
              If true, pins referenced in more than one port will throw 
              error.  

        Returns: 
            pins_to_ports : dictionary, key -> string; pair -> list 
              mapping pins name to the ports. Note, this data-structure
              implies that a pin can be located within two ports. If user
              wants to disallow, user need to set `no_duplicates` to True.
        """
        pins_to_ports = {} 
        for port in ports: 
            for pin in self.ports[port].pins: 
                if pin in pins_to_ports: 
                    if no_duplicates: 
                        raise RuntimeError("Pin is double referenced: %s, %s"%(pins_to_ports[pin],port))
                    pins_to_ports[pin].append(port)
                    continue 
                pins_to_ports[pin] = [port]
        return pins_to_ports

    def get_pin(self,name): 
        """This function will search through the Pins and Groups to return a 
        a list of all the pins associated with the name. A single pin will yield 
        a list with one string, but a group can produce the same; if the group
        contains only one pin. The difference for the group though is that the 
        name of the group will be different than the single name in the list. 

        Returns
          pinlist : list of string, the pin names 
 
          pintype : string indicating if name was a 'pin' or 'group'.

          If name is not found, and empty list and string will be returned.
        """
        # Search DFPNs first 
        for pin in self.pins: 
            if name == pin.name: return [pin.name], "pin"
        # Search the DGGP and DFGE second 
        for grp in self.groups: 
            if grp.name == name:  
                return grp.pins, "group" 
        return [],""
      
    # ------------------------------------------------------------------------: 
    def summary(self,mask=False): 
        """ 
        Report high-level information related to the config object.
        Parameter: 
          mask : bool, default = False
            If true, the source file path will be masked from reporting.
        """
        func = "st7p.config.summary"
        print("\n" + "-"*(func.__len__()+2) + ":")
        print(""+func + "  :");print("-"*(func.__len__()+2) + ":")
        if mask: print("[%s]: Source-path: %s"%(func, "<masked>"))
        else:    print("[%s]: Source-path: %s"%(func, self._abs_path))
        print("[%s]: Number of sites: %s" %(func, self.sites))
        print("[%s]: Number of pins: %s"  %(func,self.pins.length()))
        print("[%s]: Number of ports: %s" %(func,self.ports.length()))
        print("[%s]: Number of groups: %s"%(func,self.groups.length()))
        ganged = 0 ; 
        for supply in self.supplies: 
            if supply.is_ganged(): ganged +=1 
        print("[%s]: Number of power supplies: %s"%(
              func, self.supplies.length()))
        print("[%s]: Number of supplies using ganging: %s"%(
              func, ganged))
        print("[%s]: Number of utility purposes: %d"%(
              func, self.utility_purposes.length()))
        return 
    # ------------------------------------------------------------------------: 


def _dump_digital_pogos(cfo):
    pogos = {} 
    sites = cfo.sites
    for pin in cfo.pins:
        for site in range(1,cfo.sites + 1): 
            _pogos = pin.channels[site]
            for pogo in _pogos:  
                pogos[int(pogo)] = {"name":pin.name}
    pogos.keys().sort()
    for pogo in pogos: 
        print(pogo)
    return 
            
    
            

def write_pogo_report(cfo,digHW= "PS1600", ): 
    func = "func"
    for pin in cfo.pins: 
        print("%s -> %s, %s"%(pin.channel,pin.name,digHW))
    

# ----------------------------------------------------------------------------:
# Using the utility instrument: TDC: 342460
# -----------------------------------------
# First of all, you need to define the utitliy lines in the DUT board file
# as DUT signals  (not as utilityLines signals). 
#
def write_smt8(cfo,chn_attrs=None,name="",directory=""):
    """ 
    This funciton creates a SMT8 dut board description file
    from the `st7p.config.Config` object.
    """
    func = "st7p.config.write_smt8"
    if not isinstance(cfo,Config): 
        raise ValueError("'cfo' must be of type st7p.config.Config")
    #if name == "": name = "smt8_config.dbd"; name_wo_suffix = "smt8_config"
    #else: 
    #    if not name.endswith(".dbd"): name += ".dbd"
    #    name_wo_suffix = name.replace(".dbd","")


    if directory == "": 
        directory = "configuration" # os.getcwd()
        os.mkdir(directory)
        
    else: pass # TODO: Should flush this out 


    if chn_attrs: 
         if not name: 
             basename = "smt8_config"
             wo_fxd = basename + "_without_fxd"
             wi_fxd = basename + "_with_fxd"
             dbd_wo_suffix = wo_fxd
             dbd = os.path.join(directory,wo_fxd + ".dbd")  
             dbd_wi_fxd = os.path.join(directory,wi_fxd + ".dbd")

    #print("Creating dbd file at: %s"%(dbd)) 
    sites = int(cfo.sites) 


    channelToName = {}
    pinToSiteChannels = OrderedDict() 

    # cache al DFPN lines 
    digpins = []
    for pin in cfo.pins: 
        digpins.append(["signal %s {"%(pin.name)])
  
        pinToSiteChannels[pin.name] = OrderedDict()

        for site in range(1,sites+1): 
            try: 
                channels = pin.channels[site]
            except:
                raise RuntimeError("No site %s for pin %s: %s -> %s"%(site,pin.name,pin.name,pin.channels))
      
            if len(pin.channels[site]) > 1: raise RuntimeError("Not supporting ganged digtial channels yet: %s -> %s"%(pin.name, pin.channels))
            channel = pin.channels[site][0]
            digpins[-1].append("site %s { pogo = %s; }"%(site,channel))

            if channel in channelToName: 
                print("WARNING: Channel %s is being resued on site %s for pin %s"%(channel,site,pin.name))
            channelToName[channel] = pin.name 
            
            pinToSiteChannels[pin.name][site] = channel

        digpins.append(["}"]) 
    # cache all the supplies: 
    dpspins = []
    for supply in cfo.supplies: 
        dpspins.append(["signal %s {"%(supply.name)])
        for site in range(1,sites+1): 
            try: 
                channels = supply.channels[site]
            except:
                raise RuntimeError("No site %s for supply %s: %s -> %s"%(site,supply.name,supply.name,supply.channels))
            if len(channels) > 1: channels = "|".join(supply.channels[site])
            else: channels = supply.channels[site][0]
            dpspins[-1].append("site %s { pogo = %s; }"%(site,channels))
        dpspins.append(["}"]) 
    # TODO: how to store: PSLC, DFDM, PSRG, PSVD, PSSF
    

    # cache all your utility lines
    utillines = []; util_channels = set()
    for utp in cfo.utility_purposes:
        channels = list(utp.channel_settings[1].keys())# All channels are defined in DFUP. Nothing addded in UPAS
        util_channels.update(channels)
    for channel in util_channels: 
        utillines.append(["signal UTI_%s {"%(channel)])
        for site in range(1,sites+1): 
            utillines[-1].append("site %s { @Shared pogo = %s; }"%(site,channel))
        utillines.append(["}"]) 

    # cache all port defintions: 
    portlines = []
    for port in cfo.ports: 
        if port.name == "@": continue 
        portlines.append("group %s = %s;"%(port.name, "+".join(port.pins)))

    # cache all group defintions
    grouplines = [] 
    for grp in cfo.groups: 
        grouplines.append("group %s = %s;"%(grp.name,"+".join(grp.pins)))
    
    

    ## Write the dbdb file 
    pad = "  "
    with open(dbd,"w") as writer: 
        writer.write("dutboard %s {\n"%(dbd_wo_suffix))
        writer.write("%ssites = %s;\n"%(pad,sites))
        # Write digital pins 
        writer.write("\n%s// Digital Pins -------------------------------------------------:\n"%(pad))
        for pin in digpins: 
            for i,line in enumerate(pin,start=0):
                if i == 0 or i == len(pin):  
                    writer.write("%s%s\n"%(pad,line))
                else: 
                    writer.write("%s%s\n"%(pad*2,line))

        writer.write("\n%s// Supply Pins -------------------------------------------------:\n"%(pad))
        # Write digital pins 
        for supplyblock in dpspins: 
            for i,line in enumerate(supplyblock,start=0):
                if i == 0 or i == len(supplyblock):  
                    writer.write("%s%s\n"%(pad,line))
                else: 
                    writer.write("%s%s\n"%(pad*2,line))

        writer.write("\n%s// Utility Lines: -------------------------------------------------:\n"%(pad))
        # Write util lines 
        for utl in utillines: 
            for i,line in enumerate(utl,start=0):
                if i == 0 or i == len(utl):  
                    writer.write("%s%s\n"%(pad,line))
                else: 
                    writer.write("%s%s\n"%(pad*2,line))
        # Close the dbd
        writer.write("}\n") # Close dbd


    # Write DBD with fixture delay details -----------------------------------:
    if chn_attrs:
        with open(dbd_wi_fxd,"w") as writer: 
            writer.write("import configuration.%s;\n"%(wo_fxd))
            writer.write("dutboard %s {\n"%(wi_fxd))
            writer.write("%sproperty fixtureDelay {\n"%(pad))
            
            for pin, site_chn_dict in pinToSiteChannels.items(): 
                writer.write("%s%s {\n"%(2*pad,pin))
                for site,channel in site_chn_dict.items(): 
                    writer.write("%ssite %d {\n"%(3*pad,site))
                    writer.write("%sfixtureDelay = %s ns;\n"%(4*pad,chn_attrs[channel]))
                    writer.write("%s}\n"%(3*pad))
                writer.write("%s}\n"%(2*pad))
            writer.write("%s}\n"%(pad))           
            writer.write("}\n")

 

     
        

    ## TODO: write ports_and_groups.spec
    with open(os.path.join(directory,"ports_and_groups.spec"),"w") as writer: 
        writer.write("spec ports_and_groups {\n")
        for l in portlines: 
            writer.write("%s%s\n"%(pad,l))
        for l in grouplines: 
            writer.write("%s%s\n"%(pad,l))
        writer.write("}\n") # Close dbd

    ## TODO: write the utility-purpose specs
    if cfo.utility_purposes.__len__() != 0: 
        os.mkdir(os.path.join(directory,"utility_purposes"))
    for up in cfo.utility_purposes: 
        with open(os.path.join(directory,"utility_purposes","%s.spec"%(up.name)),"w") as writer: 
            writer.write("spec %s {\n"%(up.name))
            for site,setting in up.channel_settings.items():
                for channel,value in setting.items(): 
                    if (value == "X" or value == "x"): continue
                    writer.write("  setup utility UTI_%s { value = %s; }\n"%(channel,value))
            writer.write("}\n")

    



    print("DEBUG: (%s): Size of digital channel-to-signal: %s"%(func,channelToName.__len__()))
    # Read it out for debug:
    if False:  
        with open(dbd,"r") as reader: 
            for x in reader: 
                print(x.rstrip())




def read_channel_attribute_file(sfp,debug=False): 
    """
    Reads a channel-attribute file and returns a map 
    of the channel number and fixture delay value.
    """
    func = "st7p.config.read_channel_attribute_file"
    RE_FXDL = re.compile("^FXDL\s+(?P<channel>\d+)\s*.\s*(?P<delay>[\d\.]+)")
    fxMap = OrderedDict()
    with open(sfp,"r") as fh: 
        for ln,line in enumerate(fh,start=1): 
            #print("DEBUG: (%s): [%d] %s"%(func,ln,line))
            match = RE_FXDL.search(line)
            if match: 
                channel, delay = match.groups()
                if channel in fxMap: 
                    raise RuntimeError("Channel %s already stored."%(channel))
                fxMap[channel] = delay
                #print("DEBUG: (%s): FXDL %s, %s"%(func,channel,delay))
    if debug: 
        for channel,delay in fxMap.items(): 
            print("DEBUG: (%s): FXDL %s,%s"%(func,channel,delay))
    return fxMap


# ----------------------------------------------------------------------------:
def __handle_cmdline_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", 
                        help="Increase console logging", 
                        action="store_true")
    parser.add_argument("pinconfig", help="Pin-config file path")
    args = parser.parse_args()
    if not os.path.isfile(args.pinconfig): 
        raise ValueError("Invalid file")
    return args
# ----------------------------------------------------------------------------:
if __name__ == "__main__": 
    args = __handle_cmdline_args()
    if args.debug: 
        print("DEBUG: Main st7p.pins module")
    obj = read(sfp = args.pinconfig, debug = args.debug)
    print("\nNOTE: If in interactive mode, use variable name 'obj' to"\
          " the parsed object.")




