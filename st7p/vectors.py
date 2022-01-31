"""
This module parses SmarTest 7 vectors files. This entails 
pattern-master-files (pmf) and various pattern-label-files
(burst, binl, etc.). 

"""
import os, sys, re, argparse
from collections import OrderedDict
import st7putils

# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:
# ----------------------------------------------------------------------------:

RE_HP93000_VECTOR    = re.compile("^hp93000,vector,\d\.\d$")
RE_HP93000_PMF       = re.compile("^hp93000,pattern_master_file,\d\.\d$")
RE_DMAS              = re.compile("^DMAS (?P<area>\w+),(?P<mem>\w+),(?P<size>\d+),\((?P<port>[\@\w]+)\)")
RE_SQLB              = re.compile("^SQLB ")
RE_SQLB_FULL         = re.compile("^SQLB \"(?P<lbl>[\w]+)\",(?P<lbltype>\w+),(?P<start>\d+),(?P<stop>\d+),\"(?P<wvtbl>\w+)\",\((?P<port>[\@\w]+)\)")
RE_SQPG              = re.compile("^SQPG (?P<cmdNo>\d+),(?P<instr>\w+),(?P<param1>\w*),(?P<param2>[\w\"]*),(?P<mem>\w*),\((?P<port>[\@\w]+)\)")


# "The sequnecer program is contained in a sequencer area." TDC: 96570
#   - Due to this line, i will try to focus the code into at least two objects
#     SequencerProgram and SequencerArea
# 
# "Sequencer areas are port specific. Every such area contains the programs
# of all the labels that are associated with the respective port. "
# 
# "If a pin belongs to more than one port, its memory (more precisely, the 
# memory of the tester channel that is associated with this pin in the pin 
# configuration) contains several sequencer areas" TDC: 96570
# 
#  - SAs are port specific....
# 
# "The command number of an instruction is unique within the sequencer area,
# that is, the instructions are numbered across programs, starting at 0. The 
# label definition points to the location of the sequencer program within the 
# sequencer area of the label port." 
#  - I think this is 'for a given label' that is to say, this is all reset 
#    for each label. This is evident from NV's burst labels. Each testsuite 
#    may reset the labels and sequencer areas? NO IDEA.



class SequencerArea(object): 
    def __init__(self, port): 
        self.port = port  

# The sequencer program: TDC 96571
# --------------------------------
# Sequencer programs are coded in a simple language that provides
#   * instructions for sending waveforms to the DUT
#   * instructions for changing the timing and level setup during the test
#   * control structures that allow to repeat a sequence of instructions and 
#     to call a subroutine. 
# 
# ============================================================================:
class SequencerProgram(object): 
    def __init__(self,label="",port="",label_type=""):
        self.label   = label  
        self.label_type = label_type
        self.port    = port
        self.program = OrderedDict() # [cmdNo] -> {cmd:"", <dic options dependentant on cmd tye>}
        self.vectors = 0 # TODO: Proper placement? 
        self.cycles  = 0 # TODO: Proper placement? 

    def __len__(self): 
        return len(self.program)


    def add_call(self,port,cmdNo,label): 
        if port != self.port: 
           raise RuntimeError("Port mismatch: %s != %s"%(self.port,port))
        self.program[cmdNo] = {"cmd":"CALL","label":label}
   
    def add_bend(self,port,cmdNo): 
        if port != self.port: 
           raise RuntimeError("Port mismatch: %s != %s"%(self.port,port))
        self.program[cmdNo] = {"cmd":"BEND"}

    def first_cmd_num(self,): 
        return list(self.program.keys())[0]

    def last_cmd_num(self,): 
        return list(self.program.keys())[-1]


    def dump(self,):
        for cmdno, cmd in self.program.items(): 
            if cmd["cmd"] == "CALL": 
                print("SQPG %s,CALL,,\"%s\",,(%s)"%(cmdno,cmd["label"],self.port))
            if cmd["cmd"] == "BEND": 
                print("SQPG %s, BEND,,,,(%s)"%(cmdno,self.port))
       


    

    def build_from_sqpg_lines(self,sqpg_lines,start=0,stop=0):
        """ 
        The `sqpg_lines` is typically coming from a method that parsed the 
        pattern file. Thus, the keys are the line numbers. The pair is the 
        SQPG line. 

        Parameters: 
          sqpg_lines: dictionary (should be an OrderedDict)
            Keys are the line numbers from the original vector file. 
            Pairs are the SQPG lines. 

          start: int 
            The starting line coount number to start building the sequencer 
            program. The reason for this is that many SQPG lines may be contained
            in the sqpg_lines dinctionary from a multiport burst. 

          stop: int 
            Similiar reasoning as `start`
        
        """
        if stop == 0: stop = max(list(sqpg_lines.keys()))+1 
        for ln,sqpg in sqpg_lines.items():
            if ln < start: continue 
            if ln > stop:  continue 
            cmdNo = sqpg['cmd_no']
            cmd   = sqpg['instr']
            param1 = sqpg["param1"]
            param2 = sqpg["param2"]
            memory = sqpg["memory"]
            port   = sqpg["port"]
            sqpg_line = "SQPG %s,%s,%s,%s,%s,(%s)"%(cmdNo,cmd,param1,param2,memory,port)

            if port != self.port: 
                raise RuntimeError("Port mismatch amongst Sequencer Program: %s != %s; %s"%(self.port,port,self.label))

            self.program[cmdNo] = {"instr":cmd,"param1":param1,"param2":param2,"memory":memory,"port":port}
            if   cmd == "STVA": pass
            elif cmd == "STSA": pass
            elif cmd == "GENV": 
                self.vectors += int(param1) 
                self.cycles  += int(param1)
            elif cmd == "RPTV": 
                self.vectors += int(param1) 
                self.cycles  += int(param1) * int(param2)
            elif cmd == "WAIT": pass
            elif cmd == "CALL": pass
            elif cmd == "STOP": break
        return 

class MAINLabel(object): 
    def __init__(self, sfp="",name="",port="",start="",stop=""):
        self.sfp   = sfp 
        self.name  = name 
        self.port  = port 
        self.start = start # self.seq_prg.first_cmd_num()  
        self.stop  = stop  # self.seq_prg.last_cmd_num()
        self.seq_prog = SequencerProgram(label=name, port=port, label_type="MAIN")
        # NOTE: Vectors and cycles count are held in the Sequencer Program

# ============================================================================:
class Port(object): 
    """ 
    This class is to be created by Multiport Burst Labels. It is typically
    created during the processing and creation of MPBLabel objects. 
    """
    def __init__(self,port,seq_size,mem,sync_grp=""): 
        self.name = port
        self.port = port 
        self.seq_size = seq_size
        # ^^^^ This is the size, It might be easier to just store the seq prog and retuen the size?  
        self.mem = mem 
        self.seq_prog = SequencerProgram(port=port) 

        self.sync_grp = sync_grp

class Ports(st7putils.Container): 
    def __init__(self, ): 
        super(Ports,self).__init__()

    def add(self,port): 
        super(Ports,self).add(port,Port)  

# ============================================================================:

# ============================================================================:
class MPBLabel(object):
    def __init__(self,sfp):
        self.sfp  = sfp 
        self.label = os.path.basename(sfp)
        self.ports = Ports()

    def add(self,port):
        """Adds a Port object."""
        self.ports.add(port)

    def get_port_names(self):
        return self.ports.names() 

    def dump(self,): 
        print("MPBLabel.dump: Recreating %s"%(self.sfp))
        print("hp93000,vector,0.1")
        for port in self.ports: 
            print("DMAS SQPG,%s,%s,(%s)"%(port.mem,port.seq_size,port.name))
            print("SQLB \"%s\",MPBU,%s,%s,%s,(%s)"%(self.label,port.seq_prg.first_cmd_num(),port.seq_prg.last_cmd_num(),port.sync_grp,port.name))
            port.seq_prg.dump()
# ============================================================================:


# class Labels(Container):  
SQPG_INSTRS = set(["BEND", "BRKV","CALL", "CLEV", "COGO", "CTIM", 
"FLQU","GENV","JMPE","JPPS","JSUB","JTIN", "LBGN","LEND","LPBK", "MACT", "MBGN","MEAS","MEND", 
"MJPE","MRPT","NOP","PRBS","RETC","RGOP","RPTJ","RPTV","RSJP","RSUB","SRCV","SSRC","STOP","STSA",
"STVA", "TMUA","WAIT","WTER","XACT"])




# ============================================================================:
def process_dmas(line,ln=""): 
    """ 
    Returns: dictionary
      dmas['area']
      dmas['mem']
      dmas['size']
      dmas['port']
    """
    if ln == "": ln = "N/A"
    match = RE_DMAS.search(line)
    if not match: raise RuntimeError("Bad DMAS line: [%s] %s"%(ln,line))
    area, mem, size, port = match.groups()
    #print("Found DMAS: %s,%s,%s,%s"%(area,mem,size,port))
    if area == "MTST": # TDC: 98566 'SMT7.03. The MTST opt no longer has effect'
        dmas = {"area":area,"mem":mem,"size":size,"port":port} 
    elif area == "PARA" or area == "SQPG": 
        dmas = {"area":area,"mem":mem,"size":size,"port":port}
    else: raise RuntimeError("No home for DMAS line: [%d] %s"%(ln,line))
    return dmas
# ============================================================================:
# ============================================================================:
def process_sqlb(line,ln=""): 
    """
    Processes a SQLB (sequencer label definition) firmware command and returns 
    a dictionary with the following keys: 
      - "label" : label name
      - "label-type" : label type ("MAIN", "BRST", "MPBU", etc.)
      - "start-cmd" :  start command numnber identifing the position wtihin 
        the sequencer area where the label starts.
      - "stop-cmd" : the stop command number identifying the position within 
        the sequencer area where the label stops. 
      - "wf_or_sync": this parameter position can be  one of three meanings:
          * sync-group: if type has been set to MPBU, you can specify a 
            synchronization (sequencing) group for the multi-port burst 
            with this parameter. 
          * base_wf_set: the base waveform set. This waveform set is used by 
            the pattern tool to translate the physical waveform DC/DC power
            units of the vector areas into device cycle nmaes and data 
            parameters and vice versa. 
          * wavetable: the base wavetable. This wavetable is used by the 
            pattern tool to translate the physical waveform DC/DC power units
            of the vector areas into device cycle names and data parameters 
            and vice versa. 
    """
    if not line.startswith("SQLB"): 
        raise RuntimeError("Bad SQLB line: [%s] %s"%(ln,line))
    sqlb = {}
    sline    = line[5:].split(",")
    sqlb['label']      = sline[0].strip()
    sqlb['label-type'] = sline[1].strip()
    sqlb['start-cmd']  = sline[2].strip()
    sqlb['stop-cmd']   = sline[3].strip()
    sqlb['wf_or_sync'] = sline[4].strip() # NOTE: can be wf,set, wvtbl, or syn
    if   sline.__len__() == 5: sqlb['port'] = "@"
    elif sline.__len__() == 6: sqlb['port'] = sline[5].strip("()") 
    else: raise RuntimeError("Bad SQLB line: [%s] %s"%(ln,line))
    return sqlb
# ============================================================================:
# ============================================================================:
def process_sqpg(line,ln=""):
    """ 
    Returns: 
      sqpg : dictionary
        sqpg['cmd_no'] = int;  // The command number 
        sqpg["param1"] = sline[2]
        sqpg["param2"] = sline[3]
        sqpg["memory"] = sline[4]
        sqpg["port"]   = sline[5]
    """
    if ln == "": ln = "N/A"
    sqpg = OrderedDict()
    sline  = line[5:].split(",")
    sqpg["cmd_no"] = int(sline[0])
    sqpg["instr"]  = sline[1]
    sqpg["param1"] = sline[2]
    sqpg["param2"] = sline[3]
    sqpg["memory"] = sline[4]
    sqpg["port"]   = sline[5].strip("()")
    if sqpg["instr"] not in SQPG_INSTRS: 
        raise RuntimeError("bad instr '%s': [%d] %s"%(sqpg["instr"],ln,line))
    return sqpg 
# ============================================================================:
# ============================================================================:
     
def nvidia_vector_file_read(sfp,debug=False): 
    func = "nvidia_vector_file_read"

    lines = OrderedDict()
    dmas_lines = OrderedDict()
    sqlb_lines = OrderedDict()
    sqpg_lines = OrderedDict()

    main_label = False
    mpb_label  = False 

    # ------------------------------------------------------------------------:
    # This block below stores the important lines into dictionaries with line
    # number as the key and a dictionary as the pair. 
    with open(sfp,"r") as fh: 
        ln = 0
        while True:
            ln += 1
            line = fh.readline().strip() # We dont want to read all the lines in because patterns can be huge.
            if not line: break  # The running assumption is that there should not be any empty lines, if present, file is done. 
            match = RE_HP93000_VECTOR.search(line)
            if match: continue  
            # -----------------------------------------------------------------
            if line.startswith("DMAS"):    
                dmas_lines[ln] = process_dmas(ln=ln,line=line)

            elif line.startswith("SQLB"): 
                sqlb_lines[ln] = process_sqlb(ln=ln,line=line)
                if   sqlb_lines[ln]['label-type'] == "MAIN": main_label = True
                elif sqlb_lines[ln]['label-type'] == "MPBU": mpb_label = True
                else: raise RuntimeError("Bad SQLB label-type: [%d]: %s; %s"%(ln,line,sfp))

            elif line.startswith("SQPG"): 
                sqpg_lines[ln] = process_sqpg(ln=ln,line=line)
                if sqpg_lines[ln]['instr'] == "STOP": 
                    if main_label: break 
                    else: raise RuntimeError("Only expecting SQPG STOP on main labels. %s"%(sfp))
            elif line.startswith("STML"): 
                pass
                #print("WARNING: (%s): Skipping line instances: STML"%(func))
            elif line.startswith("SQLA"): 
                pass 
                #print("WARNING: (%s): Skipping line instances: SQLA"%(func))
            else: raise RuntimeError("Unaccommodated line: [%s] %s; %s"%(ln,line,sfp))
            lines[ln] = line

    # Done parsing the file
    # ---------------------------------------
    if mpb_label == main_label: 
        raise RuntimeError("MAIN and MPBU flags equal. That shouldnt be: %s"%(sfp))


    main_label_obj = None
    mpb_label_obj  = None
    if main_label: 
        port  = "" 
        start = ""
        stop  = ""
        ## ------------------------------------------------------------- START:
        ## Process DMAS commands
        if len(dmas_lines) not in [2,3]: 
            raise RuntimeError("Expecting two or three DMAS commands per MAIN label: %s"%(sfp))
        for ln, dmas in dmas_lines.items(): 
            if dmas['area'] == "MTST": continue 
            if dmas['area'] == "SQPG": dmas_sqpg_num = dmas['size']
            if dmas['area'] == "PARA": dmas_para_num = dmas['size']
            if port: 
                if dmas['port'] != port: raise RuntimeError("Port mismatch for MAIN label: %s!=%s; %s"%(dmas['port'],port,sfp))
            else: port = dmas['port']
        ## ------------------------------------------------------------- END:

        ## ------------------------------------------------------------- START:
        ## Process the the SQLB command: 
        if len(sqlb_lines) != 1: raise RuntimeError("Expecting exactly one SQLB command per MAIN label: %s"%(sfp))
        for ln,sqlb in sqlb_lines.items(): 
            if sqlb['port'] != port: raise RuntimeError("Port mismatch for MAIN label: %s!=%s; %s"%(sqlb['port'],port,sfp))
            print(sqlb)
            start = sqlb['start-cmd'] 
            stop  = sqlb['stop-cmd'] 
            #wvtbl = sqlb['wvtbl'] # TODO
            wvtbl = sqlb['wf_or_sync'] # TODO
        ## ------------------------------------------------------------- END:

        ## ------------------------------------------------------------- START:
        ## Process the SQPG commands: 
        total_sqpg_cmds = int(stop) - int(start) + 1
        if len(sqpg_lines) != (total_sqpg_cmds): 
            raise RuntimeError("Number of seq-program cmds off: %s != %s; %s"%(total_sqpg_cmds,len(sqpg_lines,sfp)))
        ## ------------------------------------------------------------- END:
        
        print(sfp,port,start)
        main_label_obj = MAINLabel(sfp=sfp,port=port,start=start,stop=stop)
        # TODO: Feed name = label name 
        main_label_obj.seq_prog.build_from_sqpg_lines(sqpg_lines)

    elif mpb_label: 
        print("DEBUG: (%s): MBP Label: %s"%(func, sfp))
        # ports[port]

        #    def __init__(self,label,port,type):
        # If all else fails, start writing sanity checks


        ## Check that DMAS and SQLB lines are equal
        if len(dmas_lines) != len(sqlb_lines): 
            raise RuntimeError("For MPB labels, we expect equal DMAS and SQLB commands: %s"%(sfp))
        ## Build ports list and checks that DMAS and SQLB are equal
        dmas_ports = set()
        sqlb_ports = set()
        for ln,dmas in dmas_lines.items(): 
            dmas_ports.add(dmas['port'])
        for ln, sqlb in sqlb_lines.items():
            if sqlb['port'] not in dmas_ports: 
                raise RuntimeError("Port is missing from DMAS: %s, %s"%(port,sfp))
            else: sqlb_ports.add(sqlb['port'])

        
        mpb_label_obj = MPBLabel(sfp=sfp)


        for ln,sqlb in sqlb_lines.items(): 
            lbl   = sqlb['label']
            start = sqlb['start-cmd']
            stop  = int(sqlb['stop-cmd'])
            port  = sqlb['port']

            seq_prog = SequencerProgram(label=lbl,label_type="MPBU",port=port)
            seq_prog.build_from_sqpg_lines(sqpg_lines,start=int(ln)+1, stop=ln+stop+1)
            #mpb_label_obj.ports[Port(name=port)] = seq_prog
            mpb_label_obj.ports.add(Port(port=port,seq_size=len(seq_prog),mem="XX"))
            mpb_label_obj.ports[port].seq_prog = seq_prog


    return main_label_obj, mpb_label_obj
          
        

            
# ============================================================================:
def read_vector_v1(sfp,debug=False): 
    """ 
    This funciton reads the vector file until the type of vector is determined
    (i.e. MAIN, BRST, MPBU, etc). At that point processing is stopped and the 
    specific reader is called. 

    Note, the linux system function grep 

    """
    func = "st7p.vectors.read_vector_v1"
    main_label = False  
    mpbu_label = False  
    with open(sfp,"r") as fh: 
        ln = 0 
        while True: 
            ln +=1
            line = fh.readline().strip()
            if not line: print("WARNING: Empty line. Stopping. ");break   
            # ^^^ NOTE The running assumption is that there should not be 
            # any empty lines, if present, file is done. 
            #print("DEBUG: (%s): [%d] %s"%(func,ln,line))
            if line.startswith("SQLB"): 
                sqlb = process_sqlb(line)
                if   sqlb['label-type'] == "MAIN": main_label = True; break 
                elif sqlb['label-type'] == "MPBU": mpbu_label = True; break 
                else: raise RuntimeError("Bad SQLB label-type: [%d]: %s; %s"%(ln,line,sfp))
    if main_label: return read_main_label(sfp,debug=debug)
    if mpbu_label: return read_mpbu_label(sfp,debug=debug)
    raise RuntimeError("No label processing found.")
# ============================================================================:
# ============================================================================:
def read_main_label(sfp,port="",debug=False): 
    func = "st7p.vectors.read_main_label"
    print("DEBUG: (%s): Processing: %s"%(func,sfp))
    main = MAINLabel(sfp)
    with open(sfp,"r") as fh: 
        ln = 0
        while True:
            ln += 1
            line = fh.readline().strip() 
            # ^^^ NOTE: We dont want to read all the lines in because patterns
            # can be huge.
            if not line: break  
            # ^^^ NOTE: The running assumption is that there should not be 
            # any empty lines, if present, file is done. 
            match = RE_HP93000_VECTOR.search(line)
            if match: continue  
            # ----------------------------------------------------------------:
            if lines.startswith("DMAS"): 
                dmas = process_dmas(ln=ln,line=line) 
                if port and port != dmas["port"]: 
                    raise RuntimeError("Port mismatch: %s != %s"(port,dmas["port"]))
                else: port = dmas["port"]
                if dmas["area"]   == "MTST": continue 
                elif dmas["area"] == "PARA": continue 
                elif dmas["area"] == "SQPG": print("TODO: FIX!") 


    return main 
# ============================================================================:
# ============================================================================:
def read_mpbu_label(sfp,debug=False):
    func = "st7p.vectors.read_mpbu_label"
    if debug: print("DEBUG: (%s): Processing: %s"%(func,sfp))
    mpb = MPBLabel(sfp)
    with open(sfp,"r") as fh: 
        for ln,line in enumerate(fh,start=1): 
            line = line.strip()
            if debug: print("DEBUG: (%s): [%s] %s"%(func,ln,line))
            if line.startswith("DMAS"): 
                dmas = process_dmas(ln=ln,line=line)
                mpb.add(Port(port=dmas["port"],mem=dmas["mem"],seq_size=dmas['size']))
                continue 
            if line.startswith("SQLB"): 
                sqlb = process_sqlb(line=line,ln=ln) 
                port = sqlb["port"]
                mpb.ports[port].sync_grp = sqlb["wf_or_sync"]
                mpb.ports[port].seq_prg.label = sqlb["label"] 
                mpb.ports[port].seq_prg.label_type = sqlb["label-type"]
                continue 
            if line.startswith("SQPG"): 
                sqpg = process_sqpg(ln=ln,line=line)
                port  = sqpg["port"]
                cmdNo = sqpg["cmd_no"]
                instr = sqpg["instr"]
                if instr == "CALL": 
                    mpb.ports[port].seq_prg.add_call(port,cmdNo,sqpg["param2"])
                elif instr == "BEND": 
                    mpb.ports[port].seq_prg.add_bend(port,cmdNo)
                else: raise RuntimeError("SQPG command '%s' not supported in MPBU processing"%(instr))
                continue 
            if RE_HP93000_VECTOR.search(line): continue 
            raise RuntimeError("Unexpected line: [%s] %s"%(ln,line))
    return mpb
# ============================================================================:
    
    

            
    

def read_vector_tmp(sfp,debug=False):
    """
    This function is built to handle NVIDA files. 
    This should be not treated as standard. Thus all outputs and processing
    is not soildified.
    """
    func = "st7p.read_vector_tmp" 
    print("\nDEBUG: (%s): Starting vector read on: %s"%(func, sfp))

    main_label  = False
    burst_label = False




    bl_port_to_main = OrderedDict()

    vectors = 0; cycles = 0; 
    with open(sfp,"r") as fh: 
        ln = 0
        while True:
            ln += 1
            line = fh.readline().strip() 
            if not line:
                print("WARNING: Found empty line in pattern. Stopping analysis")
                break   
            # ^^^ NOTE The running assumption is that there should not be 
            # any empty lines, if present, file is done. 

            print("DEBUG: (%s): [%d] %s"%(func,ln,line))
            
            # STATE PROCESSING SECTION: --------------------------------------: 
            if burst_label: 
                if line.startswith("SQPG"):
                    sqpg = process_sqpg(line,ln=ln)
                    port = sqpg['port']
                    #if port in bl_port_to_main: continue 
                    if sqpg["instr"] == "CALL": 
                        lbl  = sqpg['param2'].strip("\"")
                        if port not in bl_port_to_main: bl_port_to_main[port] = []
                        #if not bl_port_to_main[port]: 
                        #    bl_port_to_main[port] = [lbl]
                        #else: 
                        bl_port_to_main[port].append(lbl)
  
                        mpb.add_call(port,sqpg['cmd_no'],lbl)

                    elif sqpg["instr"] == "BEND": 
                        bl_port_to_main[port].append("BEND")
                    else: raise RuntimeError("unknown sqpg cmd in MPBU: [%d] %s"%(ln,line))
                continue 

            elif main_label: 
                if line.startswith("SQPG"): 
                    sqpg = process_sqpg(line,ln=ln)
                    print("DEBUG: (%s): SQPG line: [%d] %s"%(func,ln,line))

                    main_label["seq_prg"].append(line)
                    if sqpg['instr'] == "GENV":
                        vectors += int(sqpg["param1"])
                        cycles  += int(sqpg["param1"]) 
                        continue 
                    if sqpg['instr'] == "RPTV":
                        vectors += int(sqpg["param1"])
                        cycles  += int(sqpg["param1"]) * int(sqpg["param2"]) 
                        continue 
                    if sqpg["instr"] == "STOP": 
                        if not dmas_para: raise RuntimeError("No DMAS-PARA defined")
                        if not dmas_sqpg: raise RuntimeError("No DMAS-SQPG defined")
                        if dmas_para["port"] != dmas_sqpg["port"]: 
                               raise RuntimeError("DMAS port names not equal: %s != %s"%(dmas_para["port"],dmas_sqpg["port"]))

                        main_label["dmas_para"]   = dmas_para
                        main_label["dmas_sqpg"]   = dmas_sqpg
                        main_label["port_length"] = -1
                        #return {}, main_label # TODO: This should be consolidateed into a single return element and its type is checked by the caller 
                        break
                    continue 
            # FREELANCE PROCESSING SECTION: ----------------------------------: 
            match = RE_HP93000_VECTOR.search(line)
            if match: continue  
            
            match = RE_DMAS.search(line)
            if match:  
                area = match.group("area"); mem  = match.group("mem")
                size = match.group("size"); port = match.group("port")
                #print("Found DMAS: %s,%s,%s,%s"%(area,mem,size,port))
                if area == "MTST": raise RuntimeError("(%s): Found MTST area for DMAS. Skipping."%(func,line)); continue 
                if area == "PARA": dmas_para = {"mem":mem,"size":size,"port":port}; continue  
                if area == "SQPG": dmas_sqpg = {"mem":mem,"size":size,"port":port}; continue  
                raise RuntimeError("No home for DMAS line: [%d] %s"%(ln,line))
                continue 
            if line.startswith("SQLB"): 
                sline    = line[5:].split(",")
                lbl      = sline[0].strip()
                lbltype  = sline[1].strip()
                startCmd = sline[2].strip()
                stopCmd  = sline[3].strip()
                wvtbl    = sline[4].strip() # TODO: This is not necessaryily a wvtbl
                if   sline.__len__() == 5: port = "@"
                elif sline.__len__() == 6: port = sline[5].strip("()") 
                else: raise RuntimeError("Bad SQLB line: [%s] %s"%(ln,line))
                ## Analyze the SQLB intruction
                if lbltype == "MPBU": 
                    # ---------+  
                    mpb = MPBLabel(sfp)
                    mpb.add(Port(port=dmas_sqpg['port'],seq_instr=dmas_sqpg["size"],mem=dmas_sqpg["mem"]))
                    # ---------+  
                    burst_label = True;  
                    dmas_para = {}; dmas_sqpg = {} 
                    continue 
                elif lbltype == "MAIN": 
                    main_label = OrderedDict()
                    #mainlbl = MAINLabel()
                    main_label["name"]  = lbl
                    main_label["start"] = int(startCmd)
                    main_label["stop"]  = int(stopCmd)
                    main_label["wvtbl"]  = wvtbl
                    main_label["port"]  = port
                    main_label["dmas_para"]   = -1
                    main_label["dmas_sqpg"]   = -1
                    main_label["port_length"] = -1 
                    main_label["seq_prg"] = [] 
                else: raise RuntimeError("Unsupported label type: %s"%(lbltype))
                continue 
            raise RuntimeError("Unaccomodated line: [%d] %s"%(ln,line))


    # Done parsing the lines of file: 
    if burst_label: 
        print("\nDEBUG: (%s): MulitPort Burst label summary: "%(func))
        print("DEBUG: (%s): %20s | %s"%(func,"port","label"))
        print("DEBUG: (%s): ------------------------------------------------------------"%(func))
        for port, lbls in bl_port_to_main.items(): 
            for j,lbl in enumerate(lbls,start=1):
                if j == 1:  
                    print("DEBUG: (%s): %20s | %s"%(func,port,lbl))
                else: print("DEBUG: (%s): %20s | %s"%(func,"",lbl))


        print(mpb)
        print(mbp.ports)

    elif main_label: 
        print("\nDEBUG: (%s): MAIN label summary: "%(func))
        print("DEBUG: (%s): %s"%(func, main_label["name"]))
        print("DEBUG: (%s):   - start: %s, stop: %s"%(func, main_label["start"],main_label["stop"]))
        print("DEBUG: (%s):   - wvtbl: %s"%(func,main_label["wvtbl"]))
        print("DEBUG: (%s):   - port : %s"%(func,main_label["port"]))
        print("DEBUG: (%s):   - dmas_para: %s"%(func,main_label["dmas_para"]))
        print("DEBUG: (%s):   - dmas_sqpg: %s"%(func,main_label["dmas_sqpg"]))
        print("DEBUG: (%s):   - Sequencer Program: "%(func))
        for instr in main_label["seq_prg"]: 
            print("DEBUG: (%s):   -> %s"%(func,instr))

    return bl_port_to_main, main_label

            
              


    

def read_vector(sfp,debug=False):
    """Reads a vector file."""
    func = "st7p.read_vector" 

    print("DEBUG: (%s): Handing over to temprary function..."%(func))
    return read_vector_v1(sfp,debug=debug)
    return read_vector_tmp(sfp,debug=debug)

    obj = VectorFile(sfp=sfp)
    # TODO: The main question is 'how to represent a vector file in an object'. 
    # Technically speaking you have many different kinds of vector files and the 
    # true underlining structure is quite complicated. 
    # 
    # It is for this reason, I want to keep it free for now and simply gather metrics. 
    #   - filesize
    #   - dmas settings 
    #   - port -> pin list
    #   - number of vectors 
    #   - number of cycles.  
    #   - ? xmode 



             

               

    burst_labels = OrderedDict()
    # bls[lbl][port1] = [call commands, ignoring bend]
 
    dmas_para = None 
    dmas_sqpg = None 
    # ^^^ NOTE: For now, we are running a 'lst defined' approach. These are dictionaries. 
    # They need to be separate because binls will have each but bursts will only be single. 
   
    labels = []
    
    with open(sfp,"r") as fh: 
        ln = 0
        while True:
            ln += 1
            line = fh.readline().strip() # We dont want to read all the lines in because patterns can be huge.
            if not line: break  # The running assumption is that there should not be any empty lines, if present, file is done. 
            """ Processing: ----------------------------------------------- """ 
            match = RE_HP93000_VECTOR.search(line)
            if match: continue  
            """ DMAS Section: """
            match = RE_DMAS.search(line)
            if match:  
                area = match.group("area"); 
                mem  = match.group("mem")
                size = match.group("size"); 
                port = match.group("port")
                #print("Found DMAS: %s,%s,%s,%s"%(area,mem,size,port))
                if area == "MTST": 
                    print("WARNING: (%s): Found MTST area for DMAS. Skipping."%(func,line))
                    continue 
                if area == "PARA": 
                    dmas_para = {"mem":mem,"size":size,"port":port}; continue  
                if area == "SQPG":  
                    dmas_sqpg = {"mem":mem,"size":size,"port":port}; continue  
                continue 
            if line.startswith("SQLB"): 
                sline = line[5:].split(",")
                lbl     = sline[0].strip()
                lbltype = sline[1].strip()
                startCmd = sline[2].strip()
                stopCmd = sline[3].strip()
                wvtbl    = sline[4].strip() # TODO: This is not necessaryily a wvtbl
                if   sline.__len__() == 5: port = "@"
                elif sline.__len__() == 6: port = sline[5].strip("()") 
                else: raise RuntimeError("Bad SQLB line: [%s] %s"%(ln,line))
                ## Analyze the SQLB intruction
                if lbltype == "MPBU": 
                    if mpbu_labels: 
                        mpbu_label.add_port(port)

                    sync = wvtbl # NOTE: for MPBU, there is not no wvtbl entry. its the sequencer group
                    labels[MPBULabel(name=lbl,start=startCmd,stop=stopCmd,sync=sync,port=port)]
                    labels[-1].dmas_para = dmas_para
                    labels[-1].dmas_para = dmas_para
    


                    burst_label = lbl
                    print("DEBUG: (%s): This is a burst label"%(func))
                    print(port)
                    if lbl in burst_labels: 
                        burst_labels[lbl]["ports"][port] = []
                    else: 
                        burst_labels[lbl] = {"ports":{port:[]}}
                    print(burst_labels[lbl]["ports"].keys())
                    continue 
            match = RE_SQPG.search(line)
            if match: 
                cmdno  = match.group("cmdNo")
                instr  = match.group("instr")
                param1 = match.group("param1")
                param2 = match.group("param2")
                mem    = match.group("mem")
                port   = match.group("port")
                print("Found SQPG: %s,%s,%s,%s,%s,%s"%(cmdno,instr,param1,param2,mem,port))
                if burst_labels: 
                    print(burst_labels[lbl]["ports"])
                    burst_labels[lbl]["ports"][port].append(line)
                if instr == "STOP": break
                continue 
            raise RuntimeError("Unaccomodated line: [%d] %s"%(ln,line))


        if burst_labels: 
            print("")
            #print(burst_labels[lbl])
            for port in burst_labels[lbl]["ports"]:
                print(port,burst_labels[lbl]["ports"][port])
    return obj 
                

class VectorFile(object): 
    def __init__(self,sfp="",debug=False): 
        if sfp:  self._abspath, self._ddpath, self._filename = st7putils._93k_file_handler(sfp, "vectors")
        else:    self._abspath = ""; self._ddpath = ""; self._filename = ""; 

        self._lines = OrderedDict() # ln -> obj 

    def _add_line(self, ln, obj): 
        if ln in self._lines.keys():
            raise RuntimeError("Double entry for ln %s"%(ln))
        self._lines[ln] = obj 


 

def read_pmf(sfp,debug=False):
    """Reads a pattern master file."""
    func = "st7p.read_pmf" 
    flg_path  = False; flg_files = False
    pmf = PMF(sfp=sfp,debug=debug)
    with open(sfp,"r") as fh: 
        lines = fh.readlines()
        for ln, line in enumerate(lines, start=1): 
            line = line.strip()
            #print(ln, line)
            if not line: continue 
            if line.startswith("--"): continue 
            """ Processing Section ---------------------------------------- """
            if line == "path:":  flg_path=True;  flg_files=False; continue;  
            if line == "files:": flg_path=False; flg_files=True;  continue; 
            if flg_path: 
                path = line 
                if path in pmf._map.keys(): continue 
                else: pmf._map[path] = []
            if flg_files: pmf._map[path].append(line)
    #print(pmf._map)
    return pmf 



                

        

def read(sfp, debug = False): 
    """Selects between a pmf and vector file."""
    
    if not os.path.isfile(sfp): 
        raise RuntimeError("Invalid file: %s"%(sfp))
    vectorfile = False; pmffile = False;
    with open(sfp,'r') as fh:
        line = fh.readline()
        match = RE_HP93000_VECTOR.search(line)
        if match: vectorfile = True 
        match = RE_HP93000_PMF.search(line)
        if match: pmffile = True 
    if not vectorfile and not pmffile: 
        raise RuntimeError("Invalid file")
    if vectorfile: obj = read_vector(sfp=sfp,debug=debug)
    if pmffile:    obj = read_pmf(sfp=sfp,debug=debug)
    return obj
        
    
class PMF(object): 
    def __init__(self,sfp="",debug=False): 
        self._debug = debug
        if sfp:  self._abs_path, self._dd_path, self._filename = st7putils._93k_file_handler(sfp, "vectors")
        else:    self._abs_path = ""; self._dd_path = ""; self._filename = ""; 
        self._map = OrderedDict()

    def length(self): 
        """Returns the number of the patterns foudn in PMF"""
        totalPats = 0
        for path in self._map:
            totalPats += len(self._map[path]) 
        return totalPats

    def __iter__(self): 
        for path in self._map: 
            for file in self._map[path]:
                yield os.path.join(path,file)

    def paths(self): 
        """Return all paths referenced"""
        return self._map.keys()
    def get(self,filename, ddpath = ""): 
        """
        Return a list of all paths+files that match filename. 
        Note, this method returns a list of concatenated paths/files
        for each filename match. 

        Option 'ddpath' stands for device-directory path, and it 
        will replace the prefix '../' on paths with its value.

        NOTE: The filename is directly fed into a regex pattern. 
        Thus the expectation is that the file name consists only
        of aphlanumeric values, or the user knows that the string
        is a regex and creates it correctly.

        NOTE: Because the testflow file leaves the suffix off, we 
        simply match from the start of the file
        """
        pathsfiles = []
        RE_MATCHER = re.compile(filename)


        RE_FILE_BURST = re.compile(filename + ".burst")
        RE_FILE_BINL  = re.compile(filename + ".binl")

        for path, files in self._map.items(): 
            for fyle in files: 
                fyleWOSuffix = fyle.split(".")[0]
                if RE_MATCHER.search(fyle): 
                    pathsfiles.append(path.rstrip("/") + "/" + fyle)
                    if ddpath and path.startswith("../"): 
                        pathsfiles[-1] = pathsfiles[-1].replace('../', ddpath + "/")
                    if RE_FILE_BURST.search(fyle): return [pathsfiles[-1]]
                    if RE_FILE_BINL.search(fyle) : return [pathsfiles[-1]]
        return pathsfiles 




    def summary(self,mask=False): 
        """ 
        Report high-level information related to the PMF object.
        Parameter: 
          mask : bool, default = False
            If true, the source file path will be masked from reporting.
        """
        func = "st7p.vectors.summary"
        print("\n" + "-"*(func.__len__()+2) + ":")
        print(""+func + "  :");print("-"*(func.__len__()+2) + ":")
        if mask: print("[%s]: Source-path: %s"%(func, "<masked>"))
        else:    print("[%s]: Source-path: %s"%(func, self._abs_path))
        print("[%s]: Number of search-directories: %s"%(func, self._map.__len__()))
        _num_of_files = 0 
        for dir,files in self._map.items():
            _num_of_files += files.__len__() 
            print("[%s]:   - %-30s -> %s num of files"%(func,dir,files.__len__()))
        print("[%s]: Number of binls referenced: %s"%(func, _num_of_files))
        return 

# ----------------------------------------------------------------------------:
def __handle_cmdline_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", 
                        help="Increase console logging", 
                        action="store_true")
    parser.add_argument("vector", help="vector file path")
    args = parser.parse_args()
    if not os.path.isfile(args.vectorfile): 
        raise ValueError("Invalid file")
    return args
# ----------------------------------------------------------------------------:
if __name__ == "__main__": 
    args = __handle_cmdline_args()
    if args.debug: 
        print("DEBUG: Main st7p.vectors module")
    obj = read(sfp=args.vector, debug=args.debug) 
    print("\nNOTE: If in interactive mode, use variable name 'obj' to"\
          " the parsed object.")

