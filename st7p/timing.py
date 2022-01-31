import os, sys, re, argparse
from collections import OrderedDict
import st7putils

# TODO: How to handle master timing files 

# -----------------------------------------------------------------------------:
RE_HP93000_TIMING    = re.compile("^hp93000,timing,\d\.\d$")
RE_EQSP_WVT          = re.compile("^EQSP TIM,WVT")
RE_EQSP_EQN          = re.compile("^EQSP TIM,EQN")
RE_EQSP_SPS          = re.compile("^EQSP TIM,SPS")

# Wavetable
RE_WAVETBL           = re.compile("^WAVETBL\s+(?P<wvtbl>[\"\w\s]+)")
RE_DEFINES           = re.compile("^DEFINES\s+(?P<ports>[\w\s]+)")
RE_PINS              = re.compile("^PINS\s+(?P<pins>[\w\s]+)")
RE_PWI_PINSCALE      = re.compile("^(?P<pwi>[0-9abcdef]+)\s+\"(?P<edges>[\!\w\:\{\}\s\.]+)\"\s*(?P<dvc>[\w\.]*)")
RE_PWI_EMPTY         = re.compile("^(?P<pwi>[0-9abcdef]+)\s+\"(?P<edges>\s*)\"\s*(?P<dvc>[\w\.]*)")



RE_BRK               = re.compile("^brk\s+\"(?P<brk>[\w\s\:]*)\"")
#NOTE: Ignoring STATEMAP; RE_STATEMAP          = re.compile("^STATEMAP")
RE_EQNSET            = re.compile("^EQNSET\s+(?P<num>\d+)\s*(?P<name>[\"\w\s]*)")
RE_TIMINGSET         = re.compile("^TIMINGSET\s+(?P<num>\d+)\s*(?P<name>[\"\w\s]*)")
RE_EDGEBLOCK_ENTRY   = re.compile("^(?P<edge>[dr]\d)\s*=\s*(?P<expr>[\w\s\.\(\)\/\*\+\-]+)")
# TODO: THis is probably only good for PinScale systems 
RE_PERIOD            = re.compile("^period\s*=\s*(?P<period>[\w\s\.\(\)\,\/\*\+]+)")
RE_FRACT             = re.compile("^fract\((?P<num>\w+)\s*,\s*(?P<den>\w+)\s*,\s*(?P<scale>\w+)\)")
RE_SPECS             = re.compile("^SPECS")
RE_SPEC_ENTRY        = re.compile("(?P<spec>\w+)\s*(?P<unit>\[[\w\s]*\])?")
RE_SPECSET           = re.compile("^SPECSET\s+(?P<num>\d+)\s*(?P<name>[\w\s\"]*)")
RE_SPECIFICATION     = re.compile("^SPECIFICATION\s+(?P<name>[\"\w\s]+)")
RE_SPECIFICATION_WCB = re.compile("^SPECIFICATION\s+(?P<name>[\"\w\s]+)\s*{")
RE_SPEC_VALUES       = re.compile("(?P<spec>\w+)\s+(?P<act>[\d\.\-\+]+)\s*(?P<min>[\d\.\-\+]*)\s*(?P<max>[\d\.\-\+]*)\s*(?P<unit>[\[\]\w\s]*)\s*#?(?P<comment>.*)")
RE_SYNC              = re.compile("^SYNC")
RE_SYNC_WCB          = re.compile("^SYNC\s+{")
RE_PHASE             = re.compile("^PHASE")
RE_SEQUENCE          = re.compile("^SEQUENCE\s+\"(?P<group>\w+)\"")
RE_CLOCK             = re.compile("^CLOCK\s+\"(?P<clk>\w+)\"")
RE_PORT              = re.compile("^PORT\s+(?P<name>\w+)")
RE_EQUATIONS         = re.compile("^EQUATIONS")
RE_EQUATION          = re.compile("^(?P<name>\w+)\s*=\s*(?P<expr>[\(\)\w\+\-\*\.\/\s]+)")
# NON SUPPORTED KEYWORDS:
RE_LOOP              = re.compile("^LOOP_[IODLE]+") # _I, _O, _I_IDLE, _O_IDLE
RE_MODECONTEXT       = re.compile("^MODECONTEXT")
# -----------------------------------------------------------------------------:

def complete_specset(specset): 
    if "eqnset"  not in specset: return False 
    if "wvtbl"   not in specset: return False 
    if "check"   not in specset: return False   
    if "specset" not in specset: return False
    if "specs"   not in specset: return False
    return True

def complete_specification(specification): 
    return 



# ============================================================================:
# TODO: Should we take in the CFO? I do believe so, other than 
# It is impossible to drill down to a per-pin comparison.
# TODO: COnsider python DataClasses comparing methods. 
def eqnset_compare(tmo,cfo,eqnset1,eqnset2,debug=False): 
    """ 
    Compares two eqnsets.
    """
    func = "st7p.timing.eqnset_compare"
    eq1 = tmo.eqnsets[eqnset1]
    eq2 = tmo.eqnsets[eqnset2]

    same = False; report = []
    # ------------------------------------------------------------------------:
    # Check is the port list for each EQNSET is the same
    ports_equal = False
    ports       = []
    if set(eq1.ports) != set(eq2.ports): 
        ports_equal = False
        ports = set(eq1.ports).intersection(eq2.ports)
    else: 
        ports_equal = True 
        ports = eq1.ports
    print("DEBUG: (%s): Ports-list: %s"%(func,ports))
    # ^^^ NOTE: We check explicity but one could use 
    # set(eq1.ports).intersection(eq2.ports) straight aways to get the proper 
    # port list but you would have the flag indicated they are different. This
    # is why we check explicity.
    # ------------------------------------------------------------------------:


    pins_to_ports = cfo.get_pins_from_ports(ports,no_duplicates = True)


    print("DEBUG: (%s): Number of pins: %s"%(func,pins_to_ports.__len__())) 
    for pin, _ports in pins_to_ports.items(): 
         #print("DEBUG: (%s): %s -> %s"%(func,pin,_ports))
         pass 


    return same,report  
        
    
    

    
    


# ============================================================================:
class TimingMasterFile(object): 
    def __init__(self,sfp="",testerfile="",debug=False): 
        self.sfp = sfp
        self.testerfile = testerfile 
        self.eqnsets = OrderedDict() # [<num>] = {"path": },
        # NOTE: The pair is not directly the path becasue the syntax allows
        # PIN_ALIAS_SET. And thus, we need a wa yto represent that if needed
        self.mp_specs = OrderedDict()
        self.wvtbls = OrderedDict()

    # NOTE: The job of the function and calss is not to check the path. 
    # That will be for the parser classes to handle. 
    def add_eqnset(self,eqnset_num,eqnset_sfp): 
        if eqnset_num in self.eqnsets: 
            raise RuntimeError("EQNSET %s already logged."%(eqnset_num))
        self.eqnsets[eqnset_num] = {"path":eqnset_sfp}
        return      

    def add_mp_spec(self,mp_spec,mp_sfp): 
        if mp_spec in self.mp_specs: 
            raise RuntimeError("MULTIPORT_SPEC %s already logged."%(mp_spec))
        self.mp_specs[mp_spec] = {"path":mp_sfp}
        return   

    def add_wvtbl(self,wvtbl,wvtbl_sfp): 
        if wvtbl in self.wvtbls: 
            raise RuntimeError("WAVETABLE %s already logged."%(wvtbl))
        self.wvtbls[wvtbl] = {"path":wvtbl_sfp} 
        return   
# ============================================================================:
 
   
            




# ============================================================================:
# Timing MASTER FILE REGEX: 
RE_TMF_HEADER     = re.compile("^hp93000,timing_master_file,0\.1")
RE_TMF_TESTERFILE = re.compile("^testerfile\s*:\s*(?P<testerfile>[\w\.]+)") 
RE_TMF_EQNSET     = re.compile("^EQNSET\s+(?P<num>\d+)\s*\:\s*(?P<sfp>[\w\/\.]+)")
RE_TMF_MP_SPEC    = re.compile("^MULTIPORT_SPEC\s+(?P<mps>[\w\"\s]+)\s*:\s*(?P<sfp>[\w\/\.]+)")
RE_TMF_WAVETABLE  = re.compile("^WAVETABLE\s+(?P<wvtbl>[\w\"\s]+)\s*:\s*(?P<sfp>[\w\/\.]+)")
# ============================================================================:
# NOTE: One way we could code this up is too load all the lines then start the 
# pasring of the various blocks. 
# 
def read_timing_master_file(sfp,debug=False): 
    """ 
    This functions parses a timing master setup file and return a single 
    Timing object. All top-level blocks (i.e. EQNSET, WAVETABLE, etc) 
    """
    func = "st7p.timing.read_timing_master_file"
    tmf = TimingMasterFile(sfp=sfp,debug=debug)
    with open(sfp,"r") as fh: 
        for ln,line in  enumerate(fh,start=1): 
            line = line.strip()

            if line.startswith("#"): continue 
            if not line            : continue 
            # ----------------------------------------------------------------:
            # Ensure TMF header file is present and correct. 
            if True: #if ln == 1: 
                if RE_TMF_HEADER.search(line): continue 
                #raise RuntimeError("Bad/No TMF header:%s, file:%s"%(line,sfp))
            # ----------------------------------------------------------------:
            # Ensure testfile line is present: 
            if True: #if ln == 2:
                match = RE_TMF_TESTERFILE.search(line)
                if match: tmf.testerfile = match.group("testerfile"); continue
                #raise RuntimeError("Bad/No testerfile:%s, file:%s"%(line,sfp))
            # ----------------------------------------------------------------:
            # ----------------------------------------------------------------:
            match = RE_TMF_EQNSET.search(line)
            if match: 
                eqnset_num = match.group("num").strip()        
                eqnset_sfp = match.group("sfp").strip()
                tmf.add_eqnset(eqnset_num,eqnset_sfp)
                continue 
            match = RE_TMF_MP_SPEC.search(line)
            if match: 
                #if line.startswith("MULTIPORT_SPEC"): 
                #mp_spec, mp_sfp = [x.strip() for x in line[15:].split(":")]
                mp_spec = match.group("mps").strip() # TODO: Note could have double quotes. Align with now timing file is parsed
                mp_sfp  = match.group('sfp').strip()
                tmf.add_mp_spec(mp_spec,mp_sfp)
                continue 
            match = RE_TMF_WAVETABLE.search(line)
            if match: 
                wvtbl_name = match.group("wvtbl").strip()        
                wvtbl_sfp  = match.group("sfp").strip()
                tmf.add_wvtbl(wvtbl_name,wvtbl_sfp)
                continue 
            raise RuntimeError("Unsupported line: %s"%(line))
    # Results: ---------------------------------------------------------------:
    print("DEBUG: (%s): Num of EQNSETs   : %s"%(func,tmf.eqnsets.__len__()))
    print("DEBUG: (%s): Num of MP-SPECs  : %s"%(func,tmf.mp_specs.__len__()))
    print("DEBUG: (%s): Num of WAVETABLEs: %s"%(func,tmf.wvtbls.__len__()))
    return tmf 
# ============================================================================:
def read_timing_file(sfp,debug=False):
    """ 

    Unsupported Keywords (for now): 
      - LOOP         : (TODO: TDC entry)
      - MODECONTEXT  : (TODO: TDC entry)
      - USE_PROTOCOL : (Timing equation file125462)
    """
 
    func = "st7p.timing.read_timing_file"
    tmo = Timing(sfp=sfp,debug=debug)
    in_eqsp_sps  = False
    in_eqsp_eqn  = False
    in_eqsp_wvt  = False
    in_specification = False  
    in_statemap = False 
    specset_queue = {}
    spf_queue = {}
    with open(sfp,"r") as fh: 
        for ln, line in enumerate(fh,start=1): 
            line = line.strip()
            if not line: continue 
            if line.startswith("#"): continue 
            if debug: print("DEBUG: (%s) [%s] %s"%(func,ln,line))
            ## Unsupported Syntax: 
            match = RE_LOOP.search(line)
            if match: raise RuntimeError("SmartLoop is currently not supported: [%d]: %s"%(ln,line))
            match = RE_MODECONTEXT.search(line)
            if match: raise RuntimeError("MODECONTEXT is currently not supported: [%d]: %s"%(ln,line))
            if line.startswith("USE_PROTOCOL"): 
                raise RuntimeError("USE_PROTOCOL is currently not supported: [%d]: %s"%(ln,line))



            if line.startswith("NOOP"): 
                if debug: print("DEBUG: (%s): Skipping instances of NOOP: [%d]: %s"%(func,ln,line))
                continue 
            ## STATES SECTION
            if in_eqsp_wvt: 
                if in_statemap: 
                    if   line.startswith("PINS "):    in_statemap = False 
                    elif line.startswith("WAVETBL "): in_statemap = False 
                    elif line.startswith("EQSP "):    in_statemap = False 
                    else: 
                        print("TODO: process statemap line: [%s] %s"%(ln,line))
                        #sline = line.split()
                        #physSeq    = sline[0]
                        #statechars = sline[1]
                        #xmode      = sline[2]
                        #selector   = " ".join(sline[3:])
                        tmo.wvtbls[wvtbl].pwfbs[pwfb].statemap.append(line) 
                        # ^^^ TODO: Simply store the line until we figure out
                        #     how we want to store it. 
                        continue 
                if line.startswith("STATEMAP"):
                    in_statemap = True; continue  
                    

                match = RE_WAVETBL.search(line)
                if match: wvtbl=match.group("wvtbl").strip();tmo.wvtbls.add(WAVETBL(wvtbl,sfp=sfp));continue
                match = RE_DEFINES.search(line)
                if match: tmo.wvtbls[wvtbl].ports = match.group("ports").split(); continue 
                match = RE_PINS.search(line)
                if match: 
                    pwfb = match.group("pins"); pwfbID = tmo.wvtbls[wvtbl].pwfbs._get_next_id()
                    tmo.wvtbls[wvtbl].pwfbs.add(PWFBlock(pwfb,pwfb.split(),pwfbID)); continue 

                if line.startswith("HRPF"): 
                    tmo.wvtbls[wvtbl].hrpf = True
                    line = line[5:].strip()
                    # continue processeing because the waveform needs to be processed.
                match = RE_PWI_EMPTY.search(line)
                if match: 
                    pwi, edges, dvc = match.groups()
                    edges = PWIS.process_edges(edges,classtype="pinscale",debug=debug) # TODO: How do you know its PinScale?
                    tmo.wvtbls[wvtbl].pwfbs[pwfb].pwis.add(PWI(pwi,edges,dvc)); continue 

                match = RE_PWI_PINSCALE.search(line)
                if match: 
                    pwi, edges, dvc = match.groups()
                    edges = PWIS.process_edges(edges,classtype="pinscale",debug=debug) # TODO: How do you know its PinScale?
                    tmo.wvtbls[wvtbl].pwfbs[pwfb].pwis.add(PWI(pwi,edges,dvc)); continue 
                match = RE_BRK.search(line)
                if match: 
                    tmo.wvtbls[wvtbl].pwfbs[pwfb].brk = PWIS.process_edges(match.group('brk'),classtype="pinscale",debug=debug) # TODO: How do you know its PinScale
                    continue  
                # TODO: RE_PWI_SMARTSCALE
                # TODO: TTMODE
                # NOTE: Statemapping is ignored.


            if in_eqsp_eqn: 
                #if debug: print("DEBUG: (%s): In EQSP EQN")
                match = RE_EQNSET.search(line)
                if match: 
                    eqnset,desc = [x.strip() for x in match.groups()] # NOTE: Required for spaces w/n double quotes
                    tmo.eqnsets.add(EQNSET(eqnset,desc,sfp=sfp)); 
                    continue 
                match = RE_TIMINGSET.search(line)
                if match: 
                    timset,desc = [x.strip() for x in match.groups()] # NOTE: Required for spaces w/n double quotes
                    tmo.eqnsets[eqnset].timingsets.add(TIMINGSET(timset,desc)); 
                    continue 

                match = RE_DEFINES.search(line)
                if match: tmo.eqnsets[eqnset].ports = match.group("ports").split(); continue 
                match = RE_PINS.search(line)
                if match: 
                    edgeb = match.group("pins"); edgebID = tmo.eqnsets[eqnset].timingsets[timset].edgeblocks._get_next_id()
                    tmo.eqnsets[eqnset].timingsets[timset].edgeblocks.add(EdgeBlock(edgeb,edgeb.split(),edgebID)); continue 
                match = RE_PERIOD.search(line)
                if match: tmo.eqnsets[eqnset].timingsets[timset].period = match.group("period");continue 
                match = RE_EDGEBLOCK_ENTRY.search(line)
                if match: 
                    edge, expr = match.groups()
                    tmo.eqnsets[eqnset].timingsets[timset].edgeblocks[edgeb].update(edge,expr); continue 
                match = RE_EQUATIONS.search(line) 
                if match: continue 
                match = RE_SPECS.search(line) 
                if match: continue 
                match = RE_EQUATION.search(line)
                if match: var,expr=match.groups();tmo.eqnsets[eqnset].equations[var]=expr;continue 
                match = RE_SPEC_ENTRY.search(line) 
                if match: 
                    spec,unit=match.groups();
                    if not unit: unit = ""
                    else: unit = unit.strip() 
                    if st7putils.is_valid_spec_name(spec) and spec != 'EQSP': 
                        tmo.eqnsets[eqnset].add_spec(spec,unit.strip("[] \t")); continue 
                    else: pass 
            if in_eqsp_sps:
                if in_specification: 
                    # Maintain cbs count
                    if line == "{": cbs +=1; continue   
                    if line.startswith("{"): 
                        raise RuntimeError("Weird line (not technically wrong). Signal developer: [%d]: %s"%(ln,line))
                        cbs +=1
                    if line == "}" or re.search("}\s*#",line): 
                        cbs -=1
                        if cbs == 0:   
                            #if complete_specification(): tmo.specsets.add(SPECSET.build_from_dict(specset_queue));specset_queue={}; 
                            # else: raise RuntimeError()
                            tmo.specifications.add(SPECIFICATION.build_from_dict(spf_queue))
                            spf_queue={}; 
                            in_specification = False
                        continue 
                    # Catching elements  
                    if line.startswith("CHECK"): 
                        if    spf_queue['portsets'].__len__() == 0: spf_queue['check'] = line.split()[1].strip() 
                        else: spf_queue['portsets'][-1]['check'] = line.split()[1].strip()
                        continue 
                    match = RE_EQNSET.search(line)
                    if match: 
                        eqnset,desc=match.groups()
                        spf_queue['portsets'].append({'eqnset':eqnset,'wvtbl':'','port':'','sequence':'','phase':False,'specs':OrderedDict()})
                        continue 
                    match = RE_WAVETBL.search(line)
                    if match: spf_queue['portsets'][-1]['wvtbl']=match.group('wvtbl').strip();continue
                    match = RE_PORT.search(line)
                    if match: spf_queue['portsets'][-1]['port']=match.group('name').strip();continue
                    match = RE_SYNC_WCB.search(line)
                    if match: cbs+=1; continue 
                    match = RE_SYNC.search(line)
                    if match: continue 
                    match = RE_PHASE.search(line)
                    if match: spf_queue['portsets'][-1]['phase']=True;continue
                    match = RE_SEQUENCE.search(line)
                    if match: spf_queue['portsets'][-1]['sequence']=match.group('group').strip();continue

                    match = RE_CLOCK.search(line)
                    if match: spf_queue['portsets'][-1]['clock']=match.group('clk').strip();continue

                    match = RE_SPEC_VALUES.search(line)
                    if match: 
                        sn,sa,smn,smx,su,sc=match.groups()
                        if    spf_queue['portsets'].__len__() == 0: spf_queue['specs'][sn]=[sa,smn,smx,su,sc] 
                        else: spf_queue['portsets'][-1]['specs'][sn]=[sa,smn,smx,su,sc]
                        continue
                    raise RuntimeError("in_specification: Not sure what to do with line: [%d]: %s"%(ln,line))
                else: # not in_specifcation 
                    #if debug: print("DEBUG: (%s): in single port specset section...")
                    match = RE_EQNSET.search(line)
                    if match: eqnset, _ = match.groups(); continue 
                    match = RE_WAVETBL.search(line)
                    if match: wvtbl=match.group("wvtbl").strip(); continue
                    if line.startswith("CHECK"): check = line.split()[1]; continue 
                    match = RE_SPECSET.search(line)
                    if match: specset,desc = match.groups(); tmo.specsets.add(SPECSET(eqnset=eqnset,num=specset,desc=desc,wvtbl=wvtbl,check=check,sfp=sfp)); continue 
                    match = RE_SPEC_VALUES.search(line)    
                    if match: 
                        sn,sa,smn,smx,su,sc = match.groups();
                        if st7putils.is_valid_spec_name(sn): 
                            tmo.specsets.__last__().specs.add(SPEC(name=sn,actual=sa.strip(),minimum=smn.strip(),maximum=smx.strip(),unit=su.strip("[] "),comment=sc.strip()));continue
                    if line.startswith("SPECIFICATION"): pass # TODO: NO NEED
            ## FREELANCE : ---------------------------------------------------:
            match = RE_EQSP_WVT.search(line)
            if match: clear_eqsp(ln,line); in_eqsp_wvt=True; in_eqsp_eqn=False; in_eqsp_sps=False;continue 
            match = RE_EQSP_EQN.search(line)
            if match: clear_eqsp(ln,line); in_eqsp_wvt=False; in_eqsp_eqn=True; in_eqsp_sps=False;continue 
            match = RE_EQSP_SPS.search(line)
            if match: clear_eqsp(ln,line); in_eqsp_wvt=False; in_eqsp_eqn=False; in_eqsp_sps=True;continue 
            match = RE_SPECIFICATION.search(line)
            if match: 
                spfn=match.group("name"); 
                spf_queue = {};
                spf_queue['name']     = spfn.strip()
                spf_queue['check']    = 'all'
                spf_queue['specs']    = OrderedDict() # global variables
                spf_queue['portsets'] = [] #  {'eqnset':'','wvtbl':'','sequence':'','phase':False} 
                in_specification=True;
                if RE_SPECIFICATION_WCB.search(line): cbs = 1; 
                else: cbs = 0
                continue 

            if line.startswith("hp93000,timing,0.1"): continue
            if line.startswith("@"): continue 
            if line.startswith("DCDT "): print("TODO: Not processing DCDT lines: [%d] %s"%(ln,line));continue 
            if line.startswith("SPST "): print("TODO: Not processing SPST lines: [%d] %s"%(ln,line));continue 
            if line.startswith("PCLK "): print("TODO: Not processing PCLK lines: [%d] %s"%(ln,line));continue 
            # ^^^ TODO: May want to capture this 
            if line.startswith("CLKR "): print("TODO: Not processing CLKR lines: [%d] %s"%(ln,line));continue 
            # ^^^ TODO: May want to capture this 
            if line.startswith("BWDS "): print("TODO: Not processing BWDS lines: [%d] %s"%(ln,line));continue 
            if line.startswith("ETDS "): print("TODO: Not processing ETDS lines: [%d] %s"%(ln,line));continue 
            if line.startswith("TSUX "): print("TODO: Not processing TSUX lines: [%d] %s"%(ln,line));continue 
            if line.startswith("SDSC "): print("TODO: Not processing SDSC lines: [%d] %s"%(ln,line));continue 



            raise RuntimeError("Unaccounted for line: [%d] %s"%(ln,line))
    return tmo


 

# ============================================================================:
# NOTE: To accomidate the timing-master file, I will be changing the read 
# function to assess the first line of the referenced file and pass to 
# necessary file. 
# 
# Regardless of the type of timing file, we always return a Timing object. 
# the way this will be okay is that al lthe top-level blocks will contain 
# sfp pointers to track original locations. 
def read(sfp,debug=False):  
    func = "st7p.timing.read"
    print("DEBUG: (%s): Recieved: %s"%(func,sfp))
    if not os.path.isfile(sfp): 
        raise RuntimeError("Bad/No timing file: %s"%(sfp)) 
    dir_path = os.path.dirname(sfp)    
    if dir_path.split("/")[-1] != "timing":  
        print("WARNING: (%s): Parent directory is not 'timing': %s"%(func,sfp))
    # -----------------------------------------------------------------------: 
    # Deciphyer which timing file we are dealing with. 
    timing_file = False
    timing_master_file = False  
    with open(sfp,"r") as fh: 
        for i,line in enumerate(fh,start=1): 
            if RE_TMF_HEADER.search(line): 
                timing_master_file = True 
            elif RE_HP93000_TIMING.search(line): 
                timing_file = True
            else: 
                raise RuntimeError("Timing file doesnt contains proper "\
                      "header line. line = %s, file = %s"%(line,sfp))
            break
    # -----------------------------------------------------------------------: 
    if not timing_master_file: 
        return read_timing_file(sfp=sfp,debug=debug)#Timing(sfp=sfp,debug=debug)
    if timing_master_file: 
        tmf = read_timing_master_file(sfp = sfp,debug=debug)
        tmo = Timing()
        # --------------------------------------------------------------------:
        # EQNSET: Parse each file within the tmf
        for eqnset, eqnset_dict in tmf.eqnsets.items(): 
            eqnset_sfp = eqnset_dict["path"]
            act_eqnset_sfp = "" 
            # Resolve the eqnset path: 
            relative_count = eqnset_sfp.count("../")
            if relative_count >= 1: 
                if not eqnset_sfp.startswith("../"*relative_count): 
                    raise RuntimeError("Expecting %d '../' at the start: %s"%(relative_count,eqnset_sfp))
                act_eqnset_sfp = os.path.join("/".join(dir_path.split("/")[:-relative_count]),eqnset_sfp[3*relative_count:])
                if not os.path.isfile(act_eqnset_sfp): 
                    raise RuntimeError("Bad/No file: %s"%(act_eqnset_sfp)) 
            else: 
                if not os.path.isfile(eqnset_dict['path']): 
                    raise RuntimeError("Bad/No file: EQNSET %s : %s"%(eqnset,eqnset_sfp))
                act_eqnset_sfp = eqnset_sfp
            print("DEBUG: (%s): Searching: EQNSET %s : %s"%(func,eqnset,act_eqnset_sfp))
            # Parsing timng file: 
            _tmo = read_timing_file(act_eqnset_sfp,debug=debug) 
            tmo.eqnsets.add(_tmo.eqnsets[eqnset])
            #print("TODO: Not sure how to handle SPECSET here. Revisit when necessary (if referenced from TestSuite)")


            print("DEBUG: (%s): Num-of-SPECSETs: %s"%(func,_tmo.specsets.__len__()))
            for specset in _tmo.specsets: 
                if int(specset.eqnset) == int(eqnset): tmo.specsets.add(specset); continue 
                print("WARNING: Found extra SPECSETS in Levels-master-files processing of: %s"%(act_eqnset_sfp))
                print("WARNING:   - Extra SPECSET: %s"%(specset.name))

        # --------------------------------------------------------------------:
        # --------------------------------------------------------------------:
        # WAVETBLS: 
        for wvtbl, wvtbl_dict in tmf.wvtbls.items(): 
            wvtbl_sfp = wvtbl_dict["path"]
            act_wvtbl_sfp = "" 
            # Resolve the wvtbl path: 
            relative_count = wvtbl_sfp.count("../")
            if relative_count >= 1: 
                if not wvtbl_sfp.startswith("../"*relative_count): 
                    raise RuntimeError("Expecting %d '../' at the start: %s"%(relative_count,wvtbl_sfp))
                act_wvtbl_sfp = os.path.join("/".join(dir_path.split("/")[:-relative_count]),wvtbl_sfp[3*relative_count:])
                if not os.path.isfile(act_wvtbl_sfp): 
                    raise RuntimeError("Bad/No file: %s"%(act_wvtbl_sfp)) 
            else: 
                if not os.path.isfile(wvtbl_dict['path']): 
                    raise RuntimeError("Bad/No file: WAVETABLE %s : %s"%(wvtbl,wvtbl_sfp))
                act_wvtbl_sfp = wvtbl_sfp
            print("DEBUG: (%s): Searching: EQNSET %s : %s"%(func,wvtbl,act_wvtbl_sfp))

            # Parsing timng file: 
            _tmo = read_timing_file(act_wvtbl_sfp,debug=debug) 
            tmo.wvtbls.add(_tmo.wvtbls[wvtbl])
        # --------------------------------------------------------------------:
        # SPECICATIONS
        for mp_spec, mp_spec_dict in tmf.mp_specs.items(): 
            mp_spec_sfp = mp_spec_dict["path"]
            act_mp_spec_sfp = "" 
            # Resolve the mp_spec path: 
            relative_count = mp_spec_sfp.count("../")
            if relative_count >= 1: 
                if not mp_spec_sfp.startswith("../"*relative_count): 
                    raise RuntimeError("Expecting %d '../' at the start: %s"%(relative_count,mp_spec_sfp))
                act_mp_spec_sfp = os.path.join("/".join(dir_path.split("/")[:-relative_count]),mp_spec_sfp[3*relative_count:])
                if not os.path.isfile(act_mp_spec_sfp): 
                    raise RuntimeError("Bad/No file: %s"%(act_mp_spec_sfp)) 
            else: 
                if not os.path.isfile(mp_spec_dict['path']): 
                    raise RuntimeError("Bad/No file: MULTIPORT_SPEC %s : %s"%(mp_spec,mp_spec_sfp))
                act_mp_spec_sfp = mp_spec_sfp
            print("DEBUG: (%s): Searching: SPECIFICAITON %s : %s"%(func,mp_spec,act_mp_spec_sfp))

            # Parsing timng file: 
            _tmo = read_timing_file(act_mp_spec_sfp,debug=debug) 
            tmo.specifications.add(_tmo.specifications[mp_spec])
            # TODO: Missing double quotes! really



        # EQNSET Results: 
        
        print("DEBUG: (%s): Number of EQNSETS: %s"%(func,tmo.eqnsets.__len__()))
        """
        for i,eq in enumerate(tmo.eqnsets,start=1): 
            print("%s"%(eq.sfp))
            print("EQNSET %s %s"%(eq.num,eq.desc))
            print("DEFINES %s"%(eq.ports))
            print("NUM-OF-SPECS: %s"%(eq.specs.__len__()))
            for spec,val in eq.specs.items(): 
                print("  - ",spec,val)
            print("NUM-OF-EQUATIONS: %s"%(eq.equations.__len__()))
            for eqq,expr in eq.equations.items(): 
                print("  - ",eqq,expr)
            print("NUM-OF-TIMINGSETs: %s"%(eq.timingsets.__len__()))
            for ts in eq.timingsets: 
                print("TIMINGSET: %s %s"%(ts.num,ts.desc))
                print("         : period = %s"%(ts.period))
                print("         : EDGEBLOCKS: %s"%(ts.edgeblocks.__len__()))
                for eb in ts.edgeblocks: 
                    print("         :           : %s"%(eb.pins))
                    for edge,expr in eb.edges.items(): 
                        print("         :           : %s = %s"%(edge,expr))
            if i == 12:break 
        print("%s"%(eq.sfp))
        """

        #print("DEBUG: (%s): Number of WAVETABLES: %s"%(func,tmo.wvtbls.__len__()))
        #for i,wvtbl in enumerate(tmo.wvtbls,start=1):
        #    print("  ", i,wvtbl.name) 

        #print("DEBUG: (%s): Number of SPECIFICATIONs: %s"%(func,tmo.specifications.__len__()))
        
            
            
  

        return tmo 
  
    
     

    








## UTILITY-FUNCTIONS: 


# TODO: See if this is actually useful: 
def is_action_diff(edge, act1,act2): 
     """ 
     This function compares is two actions are literally different

     Drive action examples: 
      - F00 ~= 0 
      - F10 ~= 1
      - FNO ~= !Z
      - FNZ ~= Z
      - N   ~= .

     Receive action examples: 
      - E0 ~= L
      - E1 ~= H
      - EI ~= M
      - EU ~= U 
      - EX ~= X
      - N  ~= . 

     """
     if act1 == act2: return True
     if edge == "drive": 
         if act1 == "0"   and act2 == "F00": return True # low
         if act2 == "0"   and act1 == "F00": return True
         if act1 == "1"   and act2 == "F10": return True # high 
         if act2 == "1"   and act1 == "F10": return True
         if act1 == "FNZ" and act2 == "Z":   return True # tri-state on 
         if act2 == "FNZ" and act1 == "Z":   return True
         if act1 == "FN0" and act2 == "!Z":  return True # no change tri-state on
         if act2 == "FN0" and act1 == "!Z":  return True
         if act1 == "N"   and act2 == ".":   return True # No change
         if act2 == "N"   and act1 == ".":   return True
         return False 
     elif edge == 'receive': 
         if act1 == "E0" and act2 == "L": return True
         if act2 == "E0" and act1 == "L": return True
         if act1 == "E1" and act2 == "H": return True
         if act2 == "E1" and act1 == "H": return True
         if act1 == "EI" and act2 == "M": return True
         if act2 == "EI" and act1 == "M": return True
         if act1 == "EU" and act2 == "U": return True
         if act2 == "EU" and act1 == "U": return True
         if act1 == "EX" and act2 == "X": return True
         if act2 == "EX" and act1 == "X": return True
         if act1 == "N"  and act2 == ".": return True
         if act2 == "N"  and act1 == ".": return True
     else: raise RuntimeError("Edge type %s not supported."%(edge))


def eval_specification(tmo,specification,timingsets,debug=False ):
    func = "eval_specification"

    # Type checking: ---------------------------------------------------------:
    if specification not in tmo.specifications.names(): 
        raise RuntimeError("SPECIFICATION '%s' is not contained within Timing object."%(specification))
    spf = tmo.specifications[specification]
    if not isinstance(timingsets,list): 
        raise RuntimeError("Timingsets must be list")
    if timingsets.__len__() == 1: 
        timingsets = [timingsets[0]]*spf.portsets.__len__()
    # ------------------------------------------------------------------------:

    if debug: print("DEBUG: (%s): SPECIFICATION: %s"%(func,spf.name))

    # Extract Global Specs: --------------------------------------------------:
    global_vars = OrderedDict()
    for spec in spf.specs:
        global_vars[spec.name] = float(spec.act)
        #print(" - global spec: %s = %s"%(spec.name,spec.act))
    # This logic is is that we need to first establish the global vars and 
    # their values .
    # ------------------------------------------------------------------------:
    # Per port, I need to construct a dictionary that will hold all available 
    # spec variables. 
    # 
    # It starts with going to the EQSNET and extracting the EQNSET spec 
    # variables. Here we initialze with an empty string.
    # 
    # Once you have the list of all the spec-variables for the 
    # ports EQNSET, you can initialeze them in the following order  
    #
    #  - top priority is setting the values based on the LOCAL specs
    #    for the given port. 
    # 
    #  - then, if specs are left unfilled, we set their value based on
    #    the content in the GLOBAL specs (global_vars) 
    #
    # Lastly, after setting all the spec values for the given port's EQNSET
    # we need to evalue the ENQSET's EQUATION vars. 
    #
    #
    ports = OrderedDict() 
    # ports[port1][equations][eq1] = value
    # ports[port2][equations][eq2] = value
    for i, portset in enumerate(spf.portsets): 
        if debug: print("DEBUG: (%s): Processing portset: %s"%(func,portset))
        ports[portset.name] = {"vars":'',"pin-edges":''}
        # Per portset, we combing the global_vars and the local spec + eq vars 
        #print(i,portset.name,portset.eqnset,timingsets[i])
        # Ultimately, these are the specs that need to be filled by either the
        # global vars or local vars 
        port_eqnset_specs = OrderedDict()
        # ^^^ this is to be a dictionary holding the specs for a given port's eqnset.

        # The first step is to allocate the port's eqnset specs by reading directly 
        # from the eqnset's specs. 
        for spec in tmo.eqnsets[portset.eqnset].specs: 
            port_eqnset_specs[spec] = ''
            #if debug: print("DEBUG: (%s): eqn-spec: %s"%(func,spec))

        # This step checks that no specification-port local specs are 
        for spec in portset.specs: 
            #print("  pts-spec: %s.act = %s"%(spec.name,spec.act))
            if spec.name not in port_eqnset_specs: 
                print("ERROR: Port %s is missing spec %s from eqnset %s"%(portset.name,spec.name,portset.eqnset))
            else:
                #print("  NOTE: Portset %s spec %s is being set by LOCAL value: %s"%(portset.name,spec.name,spec.act))
                port_eqnset_specs[spec.name] = float(spec.act)

        for spec,val in port_eqnset_specs.items():  
            if val == '': 
                #print("  NOTE: Portset %s spec %s is being set by GLOBAL value: %s"%(portset.name,spec,global_vars[spec]))
                port_eqnset_specs[spec] = global_vars[spec] # This will throw an Error is spec not present in global vars
            else: pass # spec already ste 

        for var, expr in tmo.eqnsets[portset.eqnset].equations.items(): 
            #print("  eqn-eqvr: %s = %s"%(var,expr))
            if expr in port_eqnset_specs: port_eqnset_specs[var] = port_eqnset_specs[expr]; continue 
            port_eqnset_specs[var] = st7putils.compute(expr,port_eqnset_specs)
            #val = compute(expr, )
        if debug:  
            print("\n:" + str("-")*78 + ":")
            print("Port Specs for %s: "%(portset.name))
            for spec,val in port_eqnset_specs.items(): 
                print("%20s : %s"%(spec,val))
            print(":" + str("-")*78 + ":\n")
        ports[portset.name]['vars'] = port_eqnset_specs
        #
        # Now go evaluate 
        things = OrderedDict()
        things['period'] = ''
        # Timingset period 
        timset = tmo.eqnsets[portset.eqnset].timingsets[timingsets[i]]
        #print("period = %s"%(timset.period)) 
        if timset.period in port_eqnset_specs: things['period']  = port_eqnset_specs[timset.period] 
        elif re.search("fract\(",timset.period): 
          match = RE_FRACT.search(timset.period)
          if not match: raise RuntimeError("Fract statement doesn't fit regex: %s"(timset.period))
          numerator, denominator, scale = match.groups() 
          period_expr = "(%s/%s)*(%s)"%(numerator,denominator,scale)
          #print("DEBUG: (%s): Reconstructed fract period statement: %s"%(func,period_expr))
          if debug: print("DEBUG: (%s): COMPUTE period expr : %s"%(func,period_expr))  
          things['period'] = st7putils.compute(period_expr,port_eqnset_specs)  
          if debug: print("DEBUG: (%s): COMPLETE period expr: %s == %s"%(func, period_expr, things["period"]))  
        else : 

            if debug: print("DEBUG: (%s): COMPUTE period expr : %s"%(func,period_expr))  
            result =  st7putils.compute(timset.period, port_eqnset_specs) #interpreter.interpret(total_vars) 
            #print("period = %s = %s"%(timset.period,result))
            things['period'] = result
            if debug: print("DEBUG: (%s): COMPLETE period expr: %s == %s"%(func, period_expr, things["period"]))  
        # TIMINGSET fract
        for eb in timset.edgeblocks:
            for edge,expr in eb.edges.items(): 
                if debug: print("DEBUG: (%s): Pin = %s, Edge = %s, Expr = %s"%(func,eb.pins, edge,expr))
                for pin in eb.pins: 
                    if pin in things: pass
                    else: things[pin] = OrderedDict()
                    if expr in port_eqnset_specs: things[pin][edge] = port_eqnset_specs[expr]  # TODO: Make sure that exprs are striped before uploaded
                    else:
                         
                        if debug: print("DEBUG: (%s): COMPUTE expr : %s"%(func,expr))  
                        things[pin][edge] = st7putils.compute(expr,port_eqnset_specs)
                        if debug: print("DEBUG: (%s): COMPLETE expr: %s == %s"%(func, expr, things[pin][edge]))  
        #print("\n:" + str("-")*78 + ":")
        #print("Port edges for %s: "%(portset.name))
        #for pin, edges in things.items():
        #    print("  ",pin,edges) 
        #print(":" + str("-")*78 + ":\n")
        ports[portset.name]['pin-edges'] = things
    ## Dump the contents of per-port 
    #for port in ports: 
    #    print("PORT: %s"%(port))
    #    for var,val in ports[port]['vars'].items(): 
    #        print("  VAR: %-20s = %s"%(var,val))
    #    for pin, edges in ports[port]['pin-edges'].items(): 
    #        if pin == "period": 
    #            print("  PERIOD: %s = %s"%(pin,edges)); continue 
    #        print("  PINS: %s"%(pin))
    #        for edge,action in edges.items():
    #            print("   %s , %s"%(edge,action))

    return ports 

# Evaluation of single-port timing specset
# TODO: I am not entirely sure what the return structures should be.
def eval_specset(tmo, specset,timingset,debug=False): 
    """ 
    Evaluate SPECSET. 

    Parameters: 
      tmo : Timing object
 
      specset : SPECSET integer identifier (note: eqnset*100 + specset)

      timingset : TIMINGSET integer identifier

    Returns: 

      total_vars : OrderedDict of all spec and equation variables 

      pinedges: OrderDict of period and pin-edge-delays settings

    """
    func = "eval_specset"
    if str(specset) not in tmo.specsets.names(): 
        raise RuntimeError("SPECSET '%s' is not contained within Timing object."%(specset))
    eqnset = tmo.specsets[specset].eqnset
    total_vars = OrderedDict() # This will contain both the  
    #eqnset_specs = OrderedDict()
    for spec in tmo.eqnsets[eqnset].specs: # Pull all but last two digits of specset
        #eqnset_specs[spec] = float(tmo.specsets[specset].specs[spec].act)
        total_vars[spec] = float(tmo.specsets[specset].specs[spec].act)
    #eq_vars = OrderedDict()
    for var,expr in tmo.eqnsets[eqnset].equations.items():
        #eq_vars[var] = expr
        #lexer = EqLexer(expr)
        #parser = EqParser(lexer)
        #interpreter = EqInterpreter(parser)
        #result = interpreter.interpret(total_vars) 
        if debug: print("DEBUG: (%s): compute var:%s, expr:%s"%(func,var,expr))
        if expr in total_vars: total_vars[var] = total_vars[expr]
        else: total_vars[var] = st7putils.compute(expr,total_vars)
        #print('  - ', var, result)

    # NOTE: This dictionary is to be returned. Note, as is, it doesnt 
    # distinguish between a spec variable and an equation variable. 
    # But this can be easily added as a sub-field to the dictionary. 

    # [pin]['d1'] = value
    # [pin]['d2'] = value
    # .
    # .
    # .
    # [pin]['d8'] = value
    #
    # [pin]['r1'] = value
    # [pin]['r2'] = value
    # .
    # .
    # .
    # [pin]['r8'] = value

    pinedges = OrderedDict()
    pinedges['period'] = ''
    # Timingset period 
    timset = tmo.eqnsets[eqnset].timingsets[timingset]
    #print("period = %s"%(timset.period)) 
    if timset.period in total_vars: pinedges['period'] = total_vars[timset.period] 
    elif re.search("fract\(",timset.period): 
          match = RE_FRACT.search(timset.period)
          if not match: raise RuntimeError("Fract statement doesn't fit regex: %s"(timset.period))
          numerator, denominator, scale = match.groups() 
          period_expr = "(%s/%s)*(%s)"%(numerator,denominator,scale)
          if debug: print("DEBUG: (%s): Reconstructed fract period statement: %s"%(func,period_expr))
          pinedges['period'] = st7putils.compute(period_expr,total_vars)  
    else : 
        pinedges['period'] = st7putils.compute(timset.period,total_vars)
    # TODO: TIMINGSET fract
    for eb in timset.edgeblocks:
        for edge,expr in eb.edges.items(): 
            #print(eb.pins, edge,expr)
            for pin in eb.pins: 
                if pin in pinedges: pass
                else: pinedges[pin] = OrderedDict()
                if expr in total_vars: pinedges[pin][edge] = total_vars[expr]  # TODO: Make sure that exprs are striped before uploaded
                else: pinedges[pin][edge] = st7putils.compute(expr,total_vars)

    return total_vars, pinedges
    
       
    
    
# -----------------------------------------------------:
class PortSet(object):
    """
    ~SPECSET for each port w/in a Multi-port timing. 
    """
    def __init__(self,port,eqnset,wvtbl,sequence="",
                 phase=False,check='all',
                 clock="",specs=None): 
        self.name = port 
        self.port = port 
        self.eqnset = eqnset
        self.wvtbl = wvtbl 
        self.sequence = sequence
        self.clock    = clock
        self.phase = phase 
        self.specs = specs
        self.check = check 
        if not specs :  self.specs = SPECS()

   
   
    def __str__(self): 
        retstr = []
        retstr.append("ENQSET: %s, WVTBL: %s, PORT: %s"%(self.eqnset,self.wvtbl,self.port))
        return "".join(retstr)

    @staticmethod
    def build_from_dict(psd):
        if "eqnset"  not in psd: raise RuntimeError("portset-dict must contain 'eqnset' entry")
        if "wvtbl"   not in psd: raise RuntimeError("portset-dict must contain 'wvtbl' entry")
        if "port"    not in psd: raise RuntimeError("portset-dict must contain 'port' entry")
        if "specs"   not in psd: raise RuntimeError("portset-dict must contain 'specs' entry")
        #if "check"   in psd: raise RuntimeError("not expecting 'check' in portset. Contact developer") 
        if "check"   not in psd: psd['check'] = 'all'
        if "sequence" not in psd: raise RuntimeError("portset-dict must contain 'sequence' entry")
        if "phase"    not in psd: raise RuntimeError("portset-dict must contain 'phase' entry")
        specs = SPECS()
        for nm,dts in psd['specs'].items(): 
            specs.add(SPEC(name=nm,actual=dts[0].strip(),minimum=dts[1].strip(),maximum=dts[2].strip(),unit=dts[3].strip("[] "),comment=dts[4]))
        return PortSet(port=psd['port'],wvtbl=psd['wvtbl'],eqnset=psd['eqnset'],sequence=psd['sequence'],phase=psd['phase'],check=psd['check'],specs=specs) 
     
        
class PortSets(st7putils.Container): 
    def __init__(self): 
        super(PortSets,self).__init__()
    def add(self, portset): 
        super(PortSets,self).add(portset,PortSet)
# -----------------------------------------------------:  
    

# ----------------------------------------------------------------------------:
class SPECIFICATION(object): 
    def __init__(self,name,check="all"): 
        self.name     = name 
        self.check    = check 
        self.specs    = SPECS() # GLOBAL
        self.portsets = PortSets()


    # TODO: SHould convert to make method look like attribute using property decorator.
    def ports(self,): 
        return [ps.port for ps in self.portsets]

    def summary(self,):
        print("Summary for multiport specificaiton: %s"%(self.name))
        for i,portset in enumerate(self.portsets,start=1): 
            print(i,portset)
       
        

    @staticmethod 
    def build_from_dict(ssd):
        if "name"     not in ssd: raise RuntimeError("specification-dict must contain 'name' entry")
        if "specs"    not in ssd: raise RuntimeError("specifcation-dict must contain 'specs' entry")
        if "portsets" not in ssd: raise RuntimeError("specification-dict must contain 'portsets' entry")
        if "check"    not in ssd: ssd['check'] = 'all'
        if ssd['portsets'].__len__() == 0: raise RuntimeError("specification-dict must contain at least one entry for portset")

        # Build spf object 
        spf = SPECIFICATION(name = ssd['name'], check=ssd['check'])

        # Build each PortSet and attach to specification object
        for ps in ssd['portsets']: 
            spf.portsets.add(PortSet.build_from_dict(ps))
        ## Build the Specs 
        specs = SPECS()
        for nm,dts in ssd['specs'].items(): 
            specs.add(SPEC(name=nm,actual=dts[0].strip(),minimum=dts[1].strip(),maximum=dts[2].strip(),unit=dts[3].strip("[] "),comment=dts[4]))
        spf.specs = specs

        return spf 
        
class SPECIFICATIONS(st7putils.Container): 
    def __init__(self): 
        super(SPECIFICATIONS,self).__init__()
    def add(self, specification): 
        super(SPECIFICATIONS,self).add(specification,SPECIFICATION)
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
def clear_eqsp(ln,line): 
    RE_EQSP_GENERAL = re.compile("EQSP\s+TIM,[WVTEQNSPS]+,\#\d+")
    if not RE_EQSP_GENERAL.search(line): 
        raise RuntimeError("EQSP line doest not adhere to strict form: [%d]: %s"%(ln,line))
    return 

# ----------------------------------------------------------------------------:
class SPEC(object):
    def __init__(self,name,actual,minimum,maximum,unit,comment): 
        self.name    = name 
        self.act     = actual  # float(actual)
        self.min     = minimum # float(minimum)
        self.max     = maximum # float(maximum)
        self.unit    = unit
        self.comment = comment.strip() 
        
class SPECS(st7putils.Container): 
    def __init__(self): 
        super(SPECS,self).__init__()
    def add(self, spec): 
        super(SPECS,self).add(spec,SPEC)
        

    
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
class SPECSET(object): 
    """SPECSET. Single-port timing setups."""
    def __init__(self,num,desc,eqnset,wvtbl,check="all",specs={},sfp=""):
        self.name   = "%s"%(int(eqnset)*100 + int(num))
        self.num    = num    # must 
        self.desc   = desc   # opt
        self.eqnset = eqnset # must 
        self.wvtbl  = wvtbl  # must 
        self.check  = check 
        if not specs: self.specs = SPECS()
        else: self.specs  = specs
        self.sfp = sfp
        
    def set_name(self,eqnset,num): 
        self.eqnset = eqnset 
        self.num    = num 
        self.name   = "%s"%(int(eqnset)*100 + int(num))

    @staticmethod 
    def build_from_dict(ssd):
        if "eqnset"  not in ssd: raise RuntimeError("specset-dict must contain 'eqnset' entry")
        if "wvtbl"   not in ssd: raise RuntimeError("specset-dict must contain 'wvtbl' entry")
        if "specset" not in ssd: raise RuntimeError("specset-dict must contain 'specset' entry")
        if "specs"   not in ssd: raise RuntimeError("specset-dict must contain 'specs' entry")
        if "check"   not in ssd: ssd['check'] = 'all'
        if "specset-desc" not in ssd: ssd['specset-desc'] = ""
        specs = SPECS()
        for nm,dts in ssd['specs'].items(): 
            specs.add(SPEC(name=nm,actual=dts[0].strip(),minimum=dts[1].strip(),maximum=dts[2].strip(),unit=dts[3].strip("[] "),comment=dts[4]))
        return SPECSET(num=ssd['specset'],desc=ssd['specset-desc'],wvtbl=ssd['wvtbl'],eqnset=ssd['eqnset'],check=ssd['check'],specs=specs) 
      

class SPECSETS(st7putils.Container): 
    def __init__(self): 
        super(SPECSETS,self).__init__()
    def add(self, specset): 
        super(SPECSETS,self).add(specset,SPECSET)
    def __getitem__(self,name): 
        return self.objects[str(name)]
# -----------------------------------------------------: 
class PWI(object): 
    def __init__(self,name,edges,dvc):
        self.name = name 
        self.pwi  = name 
        self.edges = edges
        # TODO: How wil you handle native Smart Scale edges?
        self.dvc = dvc
    def __str__(self,): 
        return "%s, recieve:%s, drive:%s, order:%s, %s"%(self.pwi,self.edges['recieve'],self.edges['drive'],self.edges['order'],self.dvc)
        #return [self.pwi,self.edges,self.dvc]

class PWIS(st7putils.Container): 
    def __init__(self): 
        super(PWIS,self).__init__()

    def add(self,pwi): 
        super(PWIS,self).add(pwi,PWI) 

    def pwis(self): 
        return list(self.objects.keys()) 

    def dvcs(self): 
        dvcs = [self.objects[pwi].dvc for pwi in self.objects.keys()] 
        return dvcs

    @staticmethod
    def process_edges(string,classtype="",debug=False): 
        """This function processes edges. 
        Currently it only supports Pin Scale format edges.
        """
        func = "process_edges"
        edges = {} 
        edges['drive'] = OrderedDict()
        edges['recieve'] = OrderedDict()
        edges['order'] = []

        xmode_syntax = re.findall("\{[\w\s\:\!]+\}",string)
        
        
        if debug: print("DEBUG: (%s): Recieved: %s"%(func,string))

        #print("DEBUG: (%s): Recieved edge def '%s' and classtype = %s"%(func,string,classtype))
        if not classtype: 
            print("WANRING: (%s): No classtype provided, Will try Pin Scale, then Native Smart Scale."%(func))
            raise RuntimeError("No class type provided.")
        if classtype == "pinscale": 
            ## Check for XMODE syntax: 
            if xmode_syntax: 
                #print("WARNING: (%s): Found curly-brackets in waveform defintion."\
                #"Removing becasue we are currently not storing STATEMAPPINGs."%(func))
                string = string.replace("{",' ')
                string = string.replace("}",' ')
            for entry in string.split(): 
                if debug: print("DEBUG: (%s): entry: %s"%(func,entry))
                edge, action = entry.split(":")
                if edge.startswith("d"): 
                    edges['drive'][edge] = {'action':action.strip(),'delay':-1}
                elif edge.startswith("r"): edges['recieve'][edge] = {'action':action.strip(),'delay':-1}
                else: raise RuntimeError("%s: Unexpected edge: %s"%(func,edge))
                edges['order'].append(edge)
        elif classtype == "smartscale": 
           print("WARNING: (%s): Smart Scale edge format not supported at the moment."%(func)) 
           raise RuntimeError("WARNING: (%s): Smart Scale edge format not supported at the moment."%(func)) 
        return edges

# ----------------------------------------------------------------------------:


      
class STATEMAPS(st7putils.Container): 
    def __init__(self): 
        super(STATEMAPS,self).__init__()
    def add(self, statemap): 
        super(STATEMAPS,self).add(statemap,STATEMAP)

class STATEMAP(object):
    """
    To display the xmodes in the Pattern Debug Tool, the wavetable contains
    the STATEMAP section. In this section the xN and x1/N modes are defined. 
  
    * physSeq: Defines the sequence of physical waveforms. Each value of the 
    physSeq column references an existing physical waveform defined in the 
    PINS section
    """
    def __init__(self,name,physSeq="",statechars="",xmode="",selector=""): 
        self.name = name 
        self.physSeq = physSeq
        self.statechars = statechars
        self.xmode = xmode
        self.selector = selector


# ----------------------------------------------------------------------------:
class PWFBlock(object): 
    def __init__(self,name,pins,ID=0):
        self.name = name # TODO: I believe the names and pins are the same.
        self.pins = pins   
        self._id  = ID # NOTE: The id is relative to the WAVETBL
        #self.pwis     = OrderedDict() # This should be a another class PWIS and pWI
        self.pwis = PWIS() 
        self.statemap = [] #  = STATEMAP(name=name)
        # [0] = {'statechar': , 'period': }


        self.brk = None
    def __str__(self): 
        return "PWFB: %s\nPWIS: %s"%(self.name,self.pwis.pwis())


    def contains(self,pin): 
        pins = self.name.split()
        for p in pins: 
            if p == pin: return True
        return False 
    def __iter__(self): 
        for pwi in self.pwis: 
            yield pwi, self.pwis[pwi]
    def __getitem__(self,pwi): 
        return self.pwis[pwi]
    def __len__(self): 
        return len(self.pwis)
    def length(self,): 
        return len(self.pwis)
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
class PWFBlocks(st7putils.Container): 

    def __init__(self): 
        super(PWFBlocks,self).__init__()
        self._ids = [] 
        self._ids_2_names = {}

    def add(self,pwfb): 
        super(PWFBlocks,self).add(pwfb,PWFBlock) 
        self._ids.append(pwfb._id)
        self._ids_2_names[pwfb._id] = pwfb.name

    # TODO: Change get method? Rather than name namee...
    # TODO: Need to make sure that there can be double defintions
    # for a given pin within a waveformtable.
    def __getitem__(self,entry): 
        return self.get(entry)

    def pins(self): 
        """Return a list of all the pins referred to"""
        pins = [] 
        for pwfb in self.objects: 
             pins.extend(self.objects[pwfb].pins)
        return pins 

    def get(self,entry):
        if entry in self.objects: return self.objects[entry]
        for pwfb in self.objects:
            pins = pwfb.split() 
            if entry in pins: return self.objects[pwfb]
            else: continue 
        raise RuntimeError("No entry for '%s'"%(entry))

    def _get_next_id(self): 
        if len(self._ids) == 0 : return 1
        else: return int(self._ids[-1] + 1)

    def contains(self,pin): 
        for pwfb in self.objects: 
            pins = pwfb.split()
            if pin in pins: return self.objects[pwfb]
        return None
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
class WAVETBL(object):
    """ 
    Attributes: 
      self.name  : string: waveformtable name
      self.ports : string-list: Ports list. DEFINES statement
      self.pwfbs : PWFBlocks : Custom container of all physical waveform blocks.    
      self.hrpf  : bool: True if 'HRPF' is present on any waveform. (default=False)  
    """
    def __init__(self,name, ports=[],hrpf=False,sfp=""): 
        self.name  = name
        self.ports = ports
        self.pwfbs = PWFBlocks()
        self.hrpf  = False 
        self.sfp   = sfp

    def __str__(self,):
        return "WAVETBL %s"%(self.name)


    def dump(self, console=False ): 
        # TODO: Dump to file 
        print("Recreate the WAVETBL defintion") 
   

    def pins(self): 
        return self.pwfbs.pins()

class WAVETBLS(st7putils.Container): 
    def __init__(self): 
        super(WAVETBLS,self).__init__()
    def add(self,wvtbl): 
        super(WAVETBLS,self).add(wvtbl,WAVETBL)
    
    def __str__(self): 
        return "WAVETBLs: %d defined\nWAVETBLs: %s"%(len(self.objects),list(self.objects.keys()))
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
class EQNSET(object): 
    def __init__(self,num,desc="",sfp=""):  
        self.name = num
        self.num  = num
        self.desc = desc
        self.sfp  = sfp # NOTE: present due to Timing Master File Setups
        self.ports      = [] # Should the default be '@'
        self.specs      = OrderedDict()
        self.equations  = OrderedDict() 
        self.timingsets = TIMINGSETS()

    def add_spec(self,spec,unit=""): 
        if spec in self.specs: 
            raise RuntimeError("Double entry for spec '%s'"%(spec))
        self.specs[spec] = unit

    def __str__(self,):
        if self.desc: 
            retstr = "EQNSET %s \"%s\""%(self.num,self.desc)
        else:
            retstr = "EQNSET %s"%(self.num)
        return retstr

class EQNSETS(st7putils.Container): 
    def __init__(self): 
        super(EQNSETS,self).__init__()
    def add(self, eqnset): 
        super(EQNSETS,self).add(eqnset,EQNSET)

    def __getitem__(self,name): 
        return self.objects[str(name)]
        



# ----------------------------------------------------------------------------:
class TIMINGSET(object): 
    def __init__(self,num,desc="",period=""): 
        self.name = num
        self.num  = num
        self.desc = desc
        self.period = period
        self.edgeblocks = EdgeBlocks() # TODO: IN Levels we call this pins block...
# ----------------------------------------------------------------------------:
class TIMINGSETS(st7putils.Container): 
    def __init__(self): 
        super(TIMINGSETS,self).__init__()
    def add(self, timingset): 
        super(TIMINGSETS,self).add(timingset,TIMINGSET)
    def __getitem__(self,name): 
        return self.objects[str(name)]
# ----------------------------------------------------------------------------:
class EdgeBlock(object): 
    def __init__(self,name,pins,ID=0):
        self.name = name # TODO: I believe the names and pins are the same.
        self.pins = pins   
        self._id  = ID # NOTE: The id is relative TIMINGSET
        self.edges     = OrderedDict()
    def update(self,edge,expr): 
        if edge in self.edges:
            raise RuntimeError("Double def for edge '%s'"%(edge)) 
        self.edges[edge] = expr
        return 
    def __iter__(self): 
        for edge in self.edges: 
            yield edge, self.edges[edge]
    def __getitem__(self,edge): 
        return self.edges[edge]
    def __len__(self): 
        return len(self.edges)
    def length(self,): 
        return len(self.edges)
    # TODO: The length should probably be reporting the number of pins
# ----------------------------------------------------------------------------:
class EdgeBlocks(st7putils.Container): 
    def __init__(self): 
        super(EdgeBlocks,self).__init__()
        self._ids = [] 
        self._ids_2_names = {}
    def add(self,edgeblock): 
        super(EdgeBlocks,self).add(edgeblock,EdgeBlock) 
        self._ids.append(edgeblock._id)
        self._ids_2_names[edgeblock._id] = edgeblock.name
    # TODO: Change get method? Rather than name namee...
    # TODO: Need to make sure that there can be double defintions
    # for a given pin within a waveformtable.
    def __getitem__(self,entry): 
        return self.get(entry)
    def get(self,entry):
        if entry in self.objects: return self.objects[entry]
        for edgeblock in self.objects:
            pins = edgeblock.split() 
            if entry in pins: return self.objects[edgeblock]
            else: continue 
        raise RuntimeError("No entry for '%s'"%(entry))

    def _get_next_id(self): 
        if len(self._ids) == 0 : return 1
        else: return int(self._ids[-1] + 1)

    def pins(self): # TODO: Add functionality to PWFBlock 
        """Return a list of all pins referenced within all edgeblocks"""
        retlist = []
        for edge in self.objects: 
            retlist.extend(self.objects[edge].pins)
        return retlist
# ----------------------------------------------------------------------------:


# ----------------------------------------------------------------------------:
class Timing(object): 
    def __init__(self,sfp="",debug=False): 
        if sfp:  
          _ = st7putils._93k_file_handler(sfp, "timing")
          self._abs_path = _[0]; self._dd_path = _[1]; self._filename = _[2]
        else: self._abs_path = ""; self._dd_path = ""; self._filename = ""; 
        self.wvtbls   = WAVETBLS() 
        self.eqnsets  = EQNSETS()
        self.specsets = SPECSETS() 
        self.specifications = SPECIFICATIONS()

    # ------------------------------------------------------------------------:
    def summary(self,mask=False): 
        """ 
        Report high-level information related to the timing object.
        Parameter: 
          mask : bool, default = False
            If true, the source file path will be masked from reporting.
        """
        func = "st7p.timing.summary"
        print("\n" + "-"*(func.__len__()+2) + ":")
        print(""+func + "  :");print("-"*(func.__len__()+2) + ":")
        if mask: print("[%s]: Source-path: %s"%(func, "<masked>"))
        else:    print("[%s]: Source-path: %s"%(func, self._abs_path))
        print("[%s]: Number of WAVETBLs: %s"%(func, self.wvtbls.length()))
        print("[%s]: Number of EQNSETs: %s"%(func, self.eqnsets.length()))
        _total_timsets = 0 
        for eqnset in self.eqnsets: 
            _total_timsets += eqnset.timingsets.length()
        print("[%s]: Number of TIMINGSETs: %s"%(func, _total_timsets))
        print("[%s]: Number of SPECSETs: %s"%(func, self.specsets.length()))
        print("[%s]: Number of SPECIFICATIONs: %s"%(
              func, self.specifications.length()))
        return 
    # ------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
def __handle_cmdline_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", 
                        help="Increase console logging", 
                        action="store_true")
    parser.add_argument("timing", help="timing file path")
    args = parser.parse_args()
    if not os.path.isfile(args.timing): 
        raise ValueError("Invalid file")
    return args
# ----------------------------------------------------------------------------:
if __name__ == "__main__": 
    args = __handle_cmdline_args()
    obj = read(sfp=args.timing, debug=args.debug) 
    print("\nNOTE: If in interactive mode, use variable name 'obj' to"\
          " the parsed object.")
