import os, sys, re, argparse
from collections import OrderedDict
import st7putils



# ----------------------------------------------------------------------------: 
RE_HP93000_LEVELS    = re.compile("^hp93000,level,\d\.\d$")
RE_EQSP_EQN      = re.compile("^EQSP LEV,EQN")
RE_EQSP_SPS      = re.compile("^EQSP LEV,SPS")
RE_EQNSET            = re.compile("^EQNSET\s+(?P<num>\d+)\s*(?P<name>[\"\w\s]*)")
RE_SPECS             = re.compile("^SPECS")
RE_SPEC_ENTRY        = re.compile("(?P<spec>\w+)\s*(?P<unit>\[[\w\s]*\])?")


RE_SPEC_VALUES       = re.compile("(?P<spec>\w+)\s+(?P<act>[\d\.\-\+]+)\s*(?P<min>[\d\.\-\+]*)\s*(?P<max>[\d\.\-\+]*)\s*(?P<unit>[\[\]\w\s]*)\s*#?(?P<comment>.*)")
RE_DPSPINS           = re.compile("^DPSPINS\s+(?P<pins>[\w\s]+)")
RE_DPS_SETTING       = re.compile("^(?P<setting>[\w]+)\s*=\s*(?P<value>.*)") # TODO: Bad, this will pick up comments
RE_LEVELSET          = re.compile("^LEVELSET\s+(?P<num>\d+)\s*(?P<name>[\"\w]*)")
RE_PINS              = re.compile("^PINS\s+(?P<pins>[\w\s\@]+)")
RE_PINLEVEL_ENTRY    = re.compile("^(?P<lvl>\w+)\s*=\s*(?P<expr>[\w\s\.\(\)\/\*\+]+)")
RE_EQUATIONS         = re.compile("^EQUATIONS")
RE_SPECSET           = re.compile("^SPECSET\s+(?P<num>\d+)\s+(?P<name>[\w\s\"]*)")





RE_EQSIGN_ENTRY    = re.compile("^(?P<var>\w+)\s*=\s*(?P<expr>[\=\w\s\.\(\)\/\*\+\-\<\>\?\:]+)")
# This can be used for both DPSPINS and PINS. When matched we have to have a 
# function that can sift it. 
RE_IOPIN_TERM      = re.compile("term\s+(?P<val>\w+)")

# ----------------------------------------------------------------------------:
RE_MODULATION        = re.compile("^MODULATION\s+(?P<num>\d+)\s+(?P<name>[\"\w]*)")
RE_PIN_ALIAS_SET     = re.compile("^PIN_ALIAS_SET")



# IO PINS Resources: TDC 16891
PIN_RESOURCES = set(['vih','vil','voh','vol','vcl','vch','v3h','vihh','vt','vth','iol','ioh'])
DPS_RESOURCES = set(['connect_state',
        't_ms',
        'ilimit', 
        'ilimit_sink', 
        'ilimit_source', 
        'iout_clamp_rng', 
        'offcurr',
        'disable_const_curr_check', 
        'ms_const_curr_disconnect',
        'current_filter_frequency', 
        'voltage_filter_frequency',
        'max_voltage_drop_force', 
        'max_voltage_drop_return',
        'modulation', 
        'mod_ilimit', 
        'mod_trig',
        'vbump', 
        'vout_b', 
        'vout_bl',
        'vout', 
        'vout_frc_rng',
        'vout_rise_settling_t_ms',
        'vout_rise_settling_t_ms_c2c', 
        'vout_fall_settling_t_ms', 
        'vout_fall_settling_t_ms_c2c',
        'vout_rise_t_ms_per_volt', 
        'vout_rise_t_ms_per_volt_c2c', 
        'vout_fall_t_ms_per_volt',
        'vout_fall_t_ms_per_volt_c2c',
        'ms_fast_preload', 
        'protect'])



def is_dps_setting(var): 
    if var in DPS_RESOURCES: return True 
    else: return False 
def is_pin_setting(var): 
    if var in PIN_RESOURCES: return True 
    else: return False 


# ============================================================================:
class LevelsMasterFile(object): 
    def __init__(self,sfp="",testerfile="",debug=False): 
        self.sfp = sfp
        self.testerfile = testerfile 
        self.eqnsets = OrderedDict() # [<num>] = {"path": },
        # NOTE: The pair is not directly the path becasue the syntax allows
        # PIN_ALIAS_SET. And thus, we need a wa yto represent that if needed
        self.testdatas = OrderedDict()

    # NOTE: The job of the function and calss is not to check the path. 
    # That will be for the parser classes to handle. 
    def add_eqnset(self,eqnset_num,eqnset_sfp): 
        if eqnset_num in self.eqnsets: 
            raise RuntimeError("EQNSET %s already logged."%(eqnset_num))
        self.eqnsets[eqnset_num] = {"path":eqnset_sfp}
        return      

    def add_testdata(self,testdata,testdata_sfp): 
        if testdata in self.testdatas: 
            raise RuntimeError("TESTDATA %s already logged."%(testdata))
        self.testdatas[testdata] = {"path":testdata_sfp}
        return   
# ============================================================================:
# ============================================================================:
# Level MASTER FILE REGEX: 
RE_LMF_HEADER     = re.compile("^hp93000,level_master_file,0\.1")
RE_LMF_TESTERFILE = re.compile("^testerfile\s*:\s*(?P<testerfile>[\w\.]+)") 
RE_LMF_EQNSET     = re.compile("^EQNSET\s+(?P<num>\d+)\s*\:\s*(?P<sfp>[\w\/\.]+)")
RE_LMF_TESTDATA   = re.compile("^TESTDATA\s+(?P<td>[\w\"\s]+)\s*:\s*(?P<sfp>[\w\/\.]+)")
def read_levels_master_file(sfp,debug=False): 
    """ 
    This functions parses a timing master setup file and return a single 
    Timing object. All top-level blocks (i.e. EQNSET, WAVETABLE, etc) 
    """
    func = "st7p.timing.read_timing_master_file"
    lmf = LevelsMasterFile(sfp=sfp,debug=debug)
    with open(sfp,"r") as fh: 
        for ln,line in  enumerate(fh,start=1): 
            line = line.strip()
            # ----------------------------------------------------------------:
            # Ensure LMF header file is present and correct. 
            if ln == 1: 
                if RE_LMF_HEADER.search(line): continue 
                raise RuntimeError("Bad/No LMF header:%s, file:%s"%(line,sfp))
            # ----------------------------------------------------------------:
            # Ensure testfile line is present: 
            if ln == 2: 
                match = RE_LMF_TESTERFILE.search(line)
                if match: lmf.testerfile = match.group("testerfile"); continue
                raise RuntimeError("Bad/No testerfile:%s, file:%s"%(line,sfp))
            # ----------------------------------------------------------------:
            if line.startswith("#"): continue 
            if not line            : continue 
            # ----------------------------------------------------------------:
            match = RE_LMF_EQNSET.search(line)
            if match: 
                eqnset_num = match.group("num").strip()        
                eqnset_sfp = match.group("sfp").strip()
                lmf.add_eqnset(eqnset_num,eqnset_sfp)
                continue 
            match = RE_LMF_TESTDATA.search(line)
            if match: 
                td  = match.group("td").strip()        
                td_sfp = match.group("sfp").strip()
                lmf.add_testdata(td,td_sfp)
                continue 
            raise RuntimeError("Unsupported line: %s"%(line))
    # Results: ---------------------------------------------------------------:
    print("DEBUG: (%s): Num of EQNSETs   : %s"%(func,lmf.eqnsets.__len__()))
    print("DEBUG: (%s): Num of TESTDATAs : %s"%(func,lmf.testdatas.__len__()))
    return lmf 
# ============================================================================:


def read_levels_file(sfp,debug=False): 
    func = "st7p.levels.read_levels_file"
    lvo = Levels(sfp=sfp)
    in_eqsp_sps=False;in_eqsp_eqn =False;
    with open(sfp,"r") as fh: 
        for ln, line in enumerate(fh,start=1): 
            line = line.strip()
            if not line: continue 
            if line.startswith("#"): continue 
            if debug: print("DEBUG: (%s) [%s] %s"%(func,ln,line))
            #if ln > 130: print("ENDING EARLY"); break
            # ----------------------------------------------------------------:
            # Blocks not translated yet: -------------------------------------:
            match = RE_MODULATION.search(line)
            if match: raise RuntimeError("MODULATION is currently not supported: [%d]: %s"%(ln,line))
            #match = RE_MODECONTEXT.search(line)
            #if match: raise RuntimeError("MODECONTEXT is currently not supported: [%d]: %s"%(ln,line))
            match = RE_PIN_ALIAS_SET.search(line)
            if match: raise RuntimeError("PIN_ALIAS_SET is currently not supported: [%d]: %s"%(ln,line))
            # ----------------------------------------------------------------:

            if in_eqsp_eqn: 
                match = RE_EQNSET.search(line)
                if match: eqnset,desc=match.groups();lvo.eqnsets.add(EQNSET(eqnset,desc,sfp=sfp));continue 
                match = RE_LEVELSET.search(line)
                if match: lvlset,desc=match.groups();lvo.eqnsets[eqnset].levelsets.add(LEVELSET(lvlset,desc));continue 
                match = RE_DPSPINS.search(line) 
                if match: 
                    dpsb = match.group("pins");dpsbID = lvo.eqnsets[eqnset].dpsblocks._get_next_id()
                    lvo.eqnsets[eqnset].dpsblocks.add(DPSBlock(dpsb,dpsb.split(),dpsbID)); continue 
                match = RE_PINS.search(line)
                if match: 
                    pinsb = match.group("pins"); pinsbID = lvo.eqnsets[eqnset].levelsets[lvlset].pinblocks._get_next_id()
                    lvo.eqnsets[eqnset].levelsets[lvlset].pinblocks.add(PinBlock(pinsb,pinsb.split(),pinsbID)); continue 
                match = RE_EQSIGN_ENTRY.search(line)
                if match: 
                    var, expr = match.groups() 
                    if is_dps_setting(var):   
                        if debug: print("DEBUG: (%s): loading DSPPINS '%s' with '%s = %s'."%(func,dpsb,var,expr))
                        lvo.eqnsets[eqnset].dpsblocks[dpsb].settings[var] = expr.strip(); continue  
                    elif is_pin_setting(var):
                        lvo.eqnsets[eqnset].levelsets[lvlset].pinblocks[pinsb].settings[var] = expr.strip(); continue  
                    elif lvo.eqnsets[eqnset].dpsblocks.__len__() == 0 and lvo.eqnsets[eqnset].levelsets.__len__() == 0:
                        lvo.eqnsets[eqnset].equations[var] = expr.strip(); continue 
                    else: raise RuntimeError("Var %s does not match with DPS or PINS settings and is not in proper location for EQUATIONS: [%d]: %s"%(var,ln,line))
                if line.startswith("term "): 
                    match = RE_IOPIN_TERM.search(line)
                    if match: lvo.eqnsets[eqnset].levelsets[lvlset].pinblocks[pinsb].settings["term"] = match.group("val").strip(); continue
                    raise RuntimeError("Term setting with unsupported setting. [%d] %s"%(ln,line))

                match = RE_SPEC_ENTRY.search(line) 
                if match: 
                    spec,unit=match.groups();
                    if not unit: unit = ""
                    else: unit = unit.strip() 
                    if line == "protect": 
                        if lvo.eqnsets[eqnset].dpsblocks.__len__() == 0: raise RuntimeError("Found 'protect' keyword but no DPS pins configured")
                        lvo.eqnsets[eqnset].dpsblocks[dpsb].settings["protect"] = True; continue  

                    if debug: print("DEBUG: (%s): Found SPEC '%s' for EQNSET %s"%(func,spec,eqnset))
                    if st7putils.is_valid_spec_name(spec) and spec != 'EQSP': 
                        # print("DEBUG: Adding spec %s. [%d] %s"%(spec,ln,line))
                        lvo.eqnsets[eqnset].add_spec(spec,unit.strip("[] \t")); continue 
                    else: pass 
                match = RE_SPECS.search(line)
                if match: continue 
                match = RE_EQUATIONS.search(line)
                if match: continue 
                #print("WARNING: (%s): No placement for line: [%d] : %s"%(func,ln,line))
            if in_eqsp_sps: 
                match = RE_EQNSET.search(line)
                if match: eqnset, _ = match.groups(); continue 
                match = RE_SPECSET.search(line)
                if match: specset,desc = match.groups(); lvo.specsets.add(SPECSET(eqnset=int(eqnset),num=specset,desc=desc,sfp=sfp)); continue 
                match = RE_SPEC_VALUES.search(line)    
                if match: 
                    sn,sa,smn,smx,su,sc = match.groups();
                    if st7putils.is_valid_spec_name(sn): 
                        lvo.specsets.__last__().specs.add(SPEC(name=sn,actual=sa.strip(),minimum=smn.strip(),maximum=smx.strip(),unit=su.strip("[] "),comment=sc.strip()));continue
                else: pass 
            ## FREELANCE 
            match = RE_EQSP_EQN.search(line)
            if match: clear_eqsp(ln,line);in_eqsp_eqn=True; in_eqsp_sps=False;continue 
            match = RE_EQSP_SPS.search(line)
            if match: clear_eqsp(ln,line);in_eqsp_eqn=False; in_eqsp_sps=True;continue 


            if RE_HP93000_LEVELS.search(line): continue 
            if line == "@": continue 
            if line.startswith("NOOP "): continue 
            if line.startswith("PSLV"): print("WARNING: (levels): not processing PSLV commands."); continue 
            if line.startswith("PSLR"): print("WARNING: (levels): not processing PSLR commands."); continue 
            if line.startswith("PSFI"): print("WARNING: (levels): not processing PSLI commands."); continue 
            if line.startswith("DRLV"): print("WARNING: (levels): not processing DRLV commands."); continue 
            if line.startswith("RCLV"): print("WARNING: (levels): not processing RCLV commands."); continue 
            if line.startswith("TERM"): print("WARNING: (levels): not processing TERM commands."); continue 
            if line.startswith("CLMP"): print("WARNING: (levels): not processing CLMP commands."); continue 
            if line.startswith("LSUX"): print("WARNING: (levels): not processing LSUX commands."); continue 
            if line.startswith("SLDO"): print("WARNING: (levels): not processing SLDO commands."); continue 
            raise RuntimeError("No placement for line: [%d] %s"%(ln,line))
    return lvo
  


def read(sfp,debug=False):  
    func = "st7p.levels.read"
    print("DEBUG: (%s): Recieved: %s"%(func,sfp))
    if not os.path.isfile(sfp): 
        raise RuntimeError("Bad/No levels file: %s"%(sfp)) 
    dir_path = os.path.dirname(sfp)    
    if dir_path.split("/")[-1] != "levels":  
        print("WARNING: (%s): Parent directory is not 'levels': %s"%(func,sfp))
    # -----------------------------------------------------------------------: 
    # Deciphyer which levels file we are dealing with. 
    levels_file = False
    levels_master_file = False  
    with open(sfp,"r") as fh: 
        for i,line in enumerate(fh,start=1): 
            if RE_LMF_HEADER.search(line): 
                levels_master_file = True 
            elif RE_HP93000_LEVELS.search(line): 
                levels_file = True
            else: 
                raise RuntimeError("Levels file doesnt contains proper "\
                      "header line. line = %s, file = %s"%(line,sfp))
            break
    # -----------------------------------------------------------------------: 
    if not levels_master_file: return read_levels_file(sfp=sfp,debug=debug)
    if levels_master_file: 
        lmf = read_levels_master_file(sfp = sfp,debug=debug)
        lvo = Levels()
        # --------------------------------------------------------------------:
        # EQNSET: Parse each file within the lmf
        _cnt = 0
        for eqnset, eqnset_dict in lmf.eqnsets.items(): 
            _cnt += 1
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
                tmppath =  os.path.join(dir_path,eqnset_dict['path'])
                if not os.path.isfile(tmppath): 
                    raise RuntimeError("Bad/No file: EQNSET %s : %s"%(eqnset,eqnset_sfp))
                act_eqnset_sfp = tmppath
            print("DEBUG: (%s): Searching: EQNSET %s : %s"%(func,eqnset,act_eqnset_sfp))
            # Parsing timng file: 
            _lvo = read_levels_file(act_eqnset_sfp,debug=debug) 
            lvo.eqnsets.add(_lvo.eqnsets[eqnset])
            # NOTE: I suppose we add every SPECSET that is pointing to the EQNSET 

            print("DEBUG: (%s): Num-of-SPECSETs: %s"%(func,_lvo.specsets.__len__()))
            for specset in _lvo.specsets: 
                if int(specset.eqnset) == int(eqnset): lvo.specsets.add(specset); continue 
                print("WARNING: Found extra SPECSETS in Levels-master-files processing of: %s"%(act_eqnset_sfp))
                print("WARNING:   - Extra SPECSET: %s"%(specset.name))
 
            #print("TODO: Not sure how to handle SPECSET here. Revisit when necessary (if referenced from TestSuite)")
            #if _cnt == 1: sys.exit(1) 
        # --------------------------------------------------------------------:
    return lvo
    


def clear_eqsp(ln,line): 
    RE_EQSP_GENERAL = re.compile("EQSP\s+LEV,[EQNSPS]+,\#\d+")
    if not RE_EQSP_GENERAL.search(line): 
        raise RuntimeError("EQSP line doest not adhere to strict form: [%d]: %s"%(ln,line))
    return 

def complete_specset(specset): 
    if "eqnset"  not in specset: return False 
    if "specset" not in specset: return False
    if "specs"   not in specset: return False
    return True

def eval_specset(lvo,specset,lvlset,debug=False): 
    """ 
    Evaluate SPECSET. 

    Parameters: 
      lvo : Levels object
 
      specset : SPECSET integer identifier (note: eqnset*100 + specset)

      lvlset : LEVELSET integer identifier

    Returns: 

      total_vars : OrderedDict of all spec and equation variables 

      pinsettings: OrderDict of period and pin-edge-delays settings

    """
    func = "st7p.levels.eval_specset"

    if str(specset) not in lvo.specsets.names(): 
        print(lvo.specsets.names())
        raise RuntimeError("SPECSET '%s' is not contained within Levels object."%(specset))
    eqnset = int(lvo.specsets[specset].eqnset)
    eqnset_sfp = lvo.eqnsets[eqnset].sfp
    if debug: print("DEBUG: (%s): Recieved: specset: %s, levelset %s"%(func,specset,lvlset))
    if debug: print("DEBUG: (%s): EQNSET:   %s, %s"%(func,eqnset,lvo.eqnsets[eqnset].desc ))
    if debug: print("DEBUG: (%s): LEVELSET: %s, %s"%(func,lvlset,lvo.eqnsets[eqnset].levelsets[lvlset].desc ))
    if debug: print("DEBUG: (%s): SPECSET:  %s, %s"%(func,specset - eqnset *100, lvo.specsets[specset].desc ))
    total_vars = OrderedDict()   
    # ------------------------------------------------------------------------:
    # Loading all SPECSET variables into internal dictionary with ACT value.
    if debug: print("DEBUG: (%s): Iterating through SPECSET's spec variables: "%(func))
    for spec in lvo.eqnsets[eqnset].specs: 
        val = float(lvo.specsets[specset].specs[spec].act)
        if debug: print("DEBUG: (%s):  - %s =  %s"%(func,spec,val))
        total_vars[spec] = float(lvo.specsets[specset].specs[spec].act)
    # ------------------------------------------------------------------------:
    # ------------------------------------------------------------------------:
    # Loop through the EQUATIONS if present
    for var,expr in lvo.eqnsets[eqnset].equations.items():
        if expr.startswith("2*( +0.25*UPHY_VIDiff +"): 
            expr = expr.replace("2*( +0.25*UPHY_VIDiff +","2*( 0.25*UPHY_VIDiff +") 
            print("WARNING: (%s): Altered expr: %s"%(func,expr))
        if expr.startswith("2*( -0.25*UPHY_VIDiff"): 
            expr = expr.replace("2*( -0.25*UPHY_VIDiff","2*( (0 - 0.25)*UPHY_VIDiff") 
            print("WARNING: (%s): Altered expr: %s"%(func,expr))
        total_vars[var] = st7putils.compute(expr,total_vars,debug=debug)
    # TODO: Note these hacks. Handling the sign before value is a current 
    #       issue. However, if not properly handled, it will (most likely)
    #       throw and error. 
    # ------------------------------------------------------------------------:
    # ------------------------------------------------------------------------:
    if debug: 
        print("DEBUG: (%s): intial load of total_vars. dumping contents: ")
        for var,val in total_vars.items():
            print("%-20s: %s"%(var,val)) 
    # ------------------------------------------------------------------------:


    pinsettings = OrderedDict()
    # ['dps']  = OrderedDict()
    # ['pins'] = OrderedDict()
    #
    # ['dps']['vcc'] = OrderedDict()
    # ['dps']['vcc'] = {'vout':xxx,'ilimit':xxx}
    # ['dps']['vdd'] = OrderedDict()
    # ['dps']['vdd'] = {'vout':xxx,'ilimit':xxx}
    # 
    # ['pins']['AA1'] = OrderedDict()
    lvlset = lvo.eqnsets[eqnset].levelsets[lvlset]
    pinsettings['dps'] = OrderedDict()
    for dpsb in lvo.eqnsets[eqnset].dpsblocks:
        for dps in dpsb.pins: 
            pinsettings['dps'][dps] = OrderedDict()
            for setting,expr in dpsb.settings.items(): 
                if setting == "offcurr": pinsettings['dps'][dps][setting] = expr; continue # THIS IS NOT A COMPUTATION
                if setting == "protect": pinsettings['dps'][dps][setting] = True; continue # THIS IS NOT A COMPUTATION
                #if setting == "term":    pinsettings['dps'][dps][setting] = expr; continue # THIS IS NOT A COMPUTATION


                #print("DEBUG: (%s): %s = %s"%(func,setting,expr))
                #print("dumping total_vars: ")
                #for s,v in total_vars.items(): 
                #    print(s,v)

                if debug: print("DEBUG: (%s): DPSPINS '%s' %s = %s"%(func,dps,setting,expr))     
                if re.search("[\?]",expr): 
                    if debug: print("DEBUG: (%s): DPS settings contains conditional operation in expresssion"%(func))
                    pinsettings['dps'][dps][setting] = 0.0; # TODO: Fix!
                    print("WARNING: (%s): Skipping conditional exprs: '%s' %s = %s"%(func,dps,setting,expr))
                    continue 

                #if expr.startswith("-0.2"): 
                #    expr.replace("-0.2","(-0.2)") 
                #    print("DEBUG: (%s): Altered expr: %s"%(expr))


                if expr in total_vars: pinsettings['dps'][dps][setting] = float(total_vars[expr])
                else: 
                    if debug: print("DEBUG: DPS setting %s = %s"%(setting,expr))
                    pinsettings['dps'][dps][setting] = st7putils.compute(expr,total_vars,debug=debug)

    if debug: 
        for dps in pinsettings['dps']: 
            for var,val in pinsettings['dps'][dps].items(): 
                print("%s : %s = %s"%(dps,var,val))

    ## Iterating through the PINS settings
    #-------------------------------------
    pinsettings['pins'] = OrderedDict()
    for pinb in lvlset.pinblocks: 
        for pin in pinb.pins: 
            pinsettings['pins'][pin] = OrderedDict()
            for setting,expr in pinb.settings.items(): 


                if setting == "term": pinsettings['pins'][pin][setting] = expr; continue # THIS IS NOT A COMPUTATION

                if expr.startswith("-0.2"): 
                    expr = expr.replace("-0.2","(0 - 0.2)") 
                    print("WARNING: (%s): Altered expr: %s"%(func,expr))
                if expr.startswith("-0.4"): 
                    expr = expr.replace("-0.4","(0 - 0.4)") 
                    print("WARNING: (%s): Altered expr: %s"%(func,expr))


                if expr in total_vars: pinsettings['pins'][pin][setting] = float(total_vars[expr])
                else: 
                    if debug: print("DEBUG: PIN %s setting %s = %s; %s"%(pin,setting,expr,eqnset_sfp))
                    pinsettings['pins'][pin][setting] = st7putils.compute(expr,total_vars,debug=debug)

    if debug: 
        for pin in pinsettings['pins']: 
            for var,val in pinsettings['pins'][pin].items(): 
                print("%s : %s = %s"%(pin,var,val))
                
    return total_vars, pinsettings




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
    def __init__(self,num,desc,eqnset,specs="",sfp=""):
        self.name   = "%s"%(int(eqnset)*100 + int(num))
        self.num    = num  # mandatory 
        self.desc   = desc # optional
        self.eqnset = int(eqnset) # mandatory
        if not specs: self.specs = SPECS()
        else: self.specs = specs  
        self.sfp = sfp 
        
    def set_name(self,eqnset,num): 
        self.eqnset = eqnset 
        self.num    = num 
        self.name   = "%s"%(int(eqnset)*100 + int(num))

    @staticmethod 
    def build_from_dict(ssd):
        if "eqnset"  not in ssd: raise RuntimeError("specset-dict must contain 'eqnset' entry")
        if "specset" not in ssd: raise RuntimeError("specset-dict must contain 'specset' entry")
        if "specs"   not in ssd: raise RuntimeError("specset-dict must contain 'specs' entry")
        if "specset-desc" not in ssd: ssd['specset-desc'] = ""
        specs = SPECS()
        for nm,dts in ssd['specs'].items(): 
            specs.add(SPEC(name=nm,actual=dts[0].strip(),minimum=dts[1].strip(),maximum=dts[2].strip(),unit=dts[3].strip("[] "),comment=dts[4]))
        return SPECSET(num=ssd['specset'],desc=ssd['specset-desc'],eqnset=int(ssd['eqnset']),specs=specs) 
      

class SPECSETS(st7putils.Container): 
    def __init__(self): 
        super(SPECSETS,self).__init__()
    def add(self, specset): 
        super(SPECSETS,self).add(specset,SPECSET)
    def __getitem__(self,name): 
        return self.objects[str(name)]
# ----------------------------------------------------------------------------:
class PinBlock(object): 
    def __init__(self,name,pins,ID=0): 
        self.name = name
        self.pins = pins # NOTE: pins shoud be the list of the name...
        self._id  = ID
        self.settings = OrderedDict()

    def update(self,setting,value): 
        if setting in self.settings: 
            raise RuntimeError("Double def for setting: %s"%(setting))
        self.settings[setting] = value 
        return 
class PinBlocks(st7putils.Container): 
    def __init__(self): 
        super(PinBlocks,self).__init__()
        self._ids = [] 
        self._ids_2_names = {}

    def add(self,pinsb): 
        super(PinBlocks,self).add(pinsb,PinBlock) 
        self._ids.append(pinsb._id)
        self._ids_2_names[pinsb._id] = pinsb.name

    def _get_next_id(self): 
        if len(self._ids) == 0 : return 1
        else: return int(self._ids[-1] + 1)

    def __getitem__(self,entry): 
        return self.get(entry)

    def get(self,entry):
        if entry in self.objects: return self.objects[entry]
        for pinsblock in self.objects:
            pins = pinsblock.split() 
            if entry in pins: return self.objects[pinsblock]
            else: continue 
        raise RuntimeError("No entry for '%s'"%(entry))
    def pins(self): # TODO: Add functionality to PWFBlock 
        """Return a list of all pins referenced within all edgeblocks"""
        retlist = []
        for pb in self.objects: 
            retlist.extend(self.objects[pb].pins)
        return retlist
# ----------------------------------------------------------------------------:

# ----------------------------------------------------------------------------:
class LEVELSET(object): 
    def __init__(self,num,desc=""): 
        self.name = num
        self.num  = num
        self.desc = desc
        self.pinblocks = PinBlocks()

    def pins(self): 
        return self.pinblocks.pins()

class LEVELSETS(st7putils.Container): 
    def __init__(self): 
        super(LEVELSETS,self).__init__()
    def add(self, levelset): 
        super(LEVELSETS,self).add(levelset,LEVELSET)
    def __getitem__(self,name): 
        return self.objects[str(name)]
# ----------------------------------------------------------------------------:

# ----------------------------------------------------------------------------:
class DPSBlock(object): 
    def __init__(self,name,pins,ID=0): 
        self.name = name
        self.pins = pins # NOTE: pins shoud be the list of the name...
        self._id  = ID
        self.settings = OrderedDict()

    def update(self,setting,value): 
        if setting in self.settings: 
            raise RuntimeError("Double def for setting: %s"%(setting))
        self.settings[setting] = value 
        return 

class DPSBlocks(st7putils.Container): 
    def __init__(self): 
        super(DPSBlocks,self).__init__()
        self._ids = [] 
        self._ids_2_names = {}

    def add(self,dpsb): 
        super(DPSBlocks,self).add(dpsb,DPSBlock) 
        self._ids.append(dpsb._id)
        self._ids_2_names[dpsb._id] = dpsb.name

    def _get_next_id(self): 
        if len(self._ids) == 0 : return 1
        else: return int(self._ids[-1] + 1)

    def __getitem__(self,entry): 
        return self.get(entry)

    def get(self,entry):
        if entry in self.objects: return self.objects[entry]
        for dpsblock in self.objects:
            pins = dpsblock.split() 
            if entry in pins: return self.objects[dpsblock]
            else: continue 
        raise RuntimeError("No entry for '%s'"%(entry))
# ----------------------------------------------------------------------------:

# ----------------------------------------------------------------------------:
class EQNSET(object): 
    def __init__(self,num,desc="",sfp=""):  
        self.name = num
        self.num  = num
        self.desc = desc
        self.dpsblocks = DPSBlocks()
        self.specs     = OrderedDict()
        self.equations = OrderedDict() 
        self.levelsets = LEVELSETS()
        self.sfp = sfp

    def add_spec(self,spec,unit=""): 
        if spec in self.specs: 
            raise RuntimeError("Double entry for spec '%s'"%(spec))
        self.specs[spec] = unit

    def __str__(self,):
        if self.desc: retstr = "EQNSET %s \"%s\""%(self.num,self.desc)
        else: retstr = "EQNSET %s"%(self.num)
        return retstr

class EQNSETS(st7putils.Container): 
    def __init__(self): 
        super(EQNSETS,self).__init__()
    def add(self, eqnset): 
        super(EQNSETS,self).add(eqnset,EQNSET)
    def __getitem__(self,name): 
        return self.objects[str(name)]
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
class Levels(object): 
    def __init__(self,sfp="",debug=False): 
        if sfp:  
          _ = st7putils._93k_file_handler(sfp, "levels")
          self._abs_path = _[0]; self._dd_path = _[1]; self._filename = _[2]
        else: self._abs_path = ""; self._dd_path = ""; self._filename = ""; 
        self.eqnsets  = EQNSETS()
        self.specsets = SPECSETS() 


    # ------------------------------------------------------------------------:
    def summary(self,mask=False): 
        """ 
        Report high-level information related to the levels object.
        Parameter: 
          mask : bool, default = False
            If true, the source file path will be masked from reporting.
        """
        func = "st7p.levels.summary"
        print("\n" + "-"*(func.__len__()+2) + ":")
        print(""+func + "  :");print("-"*(func.__len__()+2) + ":")
        if mask: print("[%s]: Source-path: %s"%(func, "<masked>"))
        else:    print("[%s]: Source-path: %s"%(func, self._abs_path))
        print("[%s]: Number of EQNSETs: %s"%(func, self.eqnsets.length()))
        _total_lvlsets = 0 
        for eqnset in self.eqnsets: 
            _total_lvlsets += eqnset.levelsets.length()
        print("[%s]: Number of LEVELSETs: %s"%(func, _total_lvlsets))
        print("[%s]: Number of SPECSETs: %s"%(func, self.specsets.length()))
        return 
    # ------------------------------------------------------------------------:



# ----------------------------------------------------------------------------:

# ----------------------------------------------------------------------------:
def __handle_cmdline_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", 
                        help="Increase console logging", 
                        action="store_true")
    parser.add_argument("levels", help="levels file path")
    args = parser.parse_args()
    if not os.path.isfile(args.levels): 
        raise ValueError("Invalid file")
    return args
# ----------------------------------------------------------------------------:
if __name__ == "__main__": 
    args = __handle_cmdline_args()
    obj = read(sfp=args.levels, debug=args.debug) 
    print("\nNOTE: If in interactive mode, use variable name 'obj' to"\
          " the parsed object.")


