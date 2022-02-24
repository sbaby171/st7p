import sys, os, re, argparse
from collections import OrderedDict
#import st7putils 
from st7p import st7putils

RE_TF_HEADER     = re.compile("^hp93000,testflow,\d\.\d")
RE_TF_LANG_REV   = re.compile("^language_revision")
RE_TEST_FLOW     = re.compile("^test_flow$")
RE_INFORMATION   = re.compile("^information$")
RE_DECLARATIONS  = re.compile("^declarations$")
RE_IMPL_DECL     = re.compile("^implicit_declarations$")
RE_FLAGS         = re.compile("^flags$")
RE_TM_PARAMS     = re.compile("^testmethodparameters$")
RE_TM_LIMITS     = re.compile("^testmethodlimits$")
RE_TMS           = re.compile("^testmethods$")
RE_END           = re.compile("^end$")
RE_TSS           = re.compile("^test_suites$")
RE_BINNING       = re.compile("^binning$")
RE_CONTEXT       = re.compile("^context$")
RE_HW_BIN_DESC   = re.compile("^hardware_bin_descriptions$")

RE_INFO_DESC  = re.compile("^description\s*=\s*\"(?P<item>.*)\"\s*;")
RE_INFO_DEV_NAME  = re.compile("^device_name\s*=\s*\"(?P<item>[\w\s]+)\"\s*;")
RE_INFO_DEV_REV   = re.compile("^device_revision\s*=\s*\"(?P<item>[\w\s]+)\"\s*;")
RE_TEST_REVISION  = re.compile("^test_revision\s*=\s*\"(?P<item>[\w\s]+)\"\s*;")

RE_DECL_TF_VAR    = re.compile("^(?P<var>\@\w+)\s*=\s*(?P<val>.*);")
RE_FLAG           = re.compile("^(?P<name>\w+)\s*=\s*(?P<val>\w+);")
RE_USER_FLAG      = re.compile("^user\s+(?P<name>\w+)\s*=\s*(?P<val>\w+);")

RE_TM_NUM         = re.compile("^(?P<tmnum>tm_\d+)\:")
RE_STR_STR        = re.compile("\"(?P<lhs>.+)\"\s*=\s*\"(?P<rhs>.*)\";")
RE_TM_LIMIT          = re.compile("\"(?P<var>[\w]+)\"\s*=\s*"\
                                  "\"(?P<lv>[\-\d\.]*)\"\s*:\s*\"(?P<lvcs>[GTELNA]+)\"\s*:\s*"\
                                  "\"(?P<hv>[\-\d\.]*)\"\s*:\s*\"(?P<hvcs>[GTELNA]+)\"\s*:\s*"\
                                  "\"(?P<unit>[\w]*)\"\s*:\s*"\
                                  "\"(?P<offset>[\d]*)\"\s*:\s*"\
                                  "\"(?P<incr>[\d]*)\";")
RE_TM_NAME        = re.compile("^testmethod_class\s*=\s*\"(?P<name>.*)\"")
RE_TS_NAME        = re.compile("^(?P<name>\w+):")
RE_TS_SETTING     = re.compile("^(?P<setting>\w+)\s*=\s*(?P<val>.+);")
# Special Test-suites: 
RE_BIN_DISCONT    = re.compile("^bin_disconnect")
RE_MULTI_BIN_DEC  = re.compile("^multi_bin_decision")



# Binning: 
RE_OW_BIN         = re.compile("^otherwise\s+bin\s*=")



RE_CONFIG         = re.compile("^context_config_file\s*=\s*\"(?P<file>[\w\.\/\\\]+)\";")
RE_TIMING         = re.compile("^context_timing_file\s*=\s*\"(?P<file>[\w\.\/\\\]+)\";")
RE_LEVELS         = re.compile("^context_levels_file\s*=\s*\"(?P<file>[\w\.\/\\\]+)\";")
RE_VECTOR         = re.compile("^context_vector_file\s*=\s*\"(?P<file>[\w\.\/\\\]+)\";")
RE_CHN_ATTR       = re.compile("^context_channel_attrib_file\s*=\s*\"(?P<file>[\w\.\/\\\]+)\";")

def read(sfp,debug=False):
    """ 
    This method will read the provided pinconfig file and return 
    context_section = False 
    the parsed object. 
    """
    func = "st7p.testflow.read"
    if debug: print("DEBUG: %s: Recieved file: %s"%(func,sfp))

    obj = Testflow(sfp)
    # WE will parse in tow passes: (1) everything but the teestflow (2) then the test flow 

    tf_lines = {"start":-1,"end":-1}
    tf_section = False; 
    info_section = False 
    decl_section = False 
    impl_decl_section = False 
    flags_section = False 
    tm_params_section = False 
    tm_limits_section = False 
    tms_section = False 
    ts_section  = False 
    binning_section = False 
    context_section = False 
    bin_disconnect_section = False
    multi_bin_decision_section = False 
    hw_bin_desc_section = False 
    # ------------------------------------------------------------------------:
    with open(sfp,"r") as fh: 
        lines = [line.strip() for line in fh.readlines()]
        for ln, line in enumerate(lines,start=1): 
            if line == '' or line.isspace(): continue 
            if line.startswith("--"): continue 
            if debug: print("DEBUG: (%s): [%d]  %s"%(func,ln,line))
            ## STATE-SECTION
            ## ---------------------------------------------------------------: 


            # Special Testsuites: 
            if bin_disconnect_section: 
                if RE_END.search(line): bin_disconnect_section=False;continue 
                match = RE_TS_SETTING.search(line)
                if match: obj.tss[tsname].add_setting(*match.groups()); continue 
                raise RuntimeError("Unsupported line in special-testsuites bin_disconnect: [%d] %s"%(ln,line)) 
            if multi_bin_decision_section: 
                if RE_END.search(line): multi_bin_decision_section=False;continue 
                match = RE_TS_SETTING.search(line)
                if match: obj.tss[tsname].add_setting(*match.groups()); continue 
                raise RuntimeError("Unsupported line in special-testsuites multi_bin_decision: [%d] %s"%(ln,line)) 
            # Special Testsuites: END

            if hw_bin_desc_section: 
                if RE_END.search(line): hw_bin_desc_section=False;continue 
                sline = line.split()
                if int(sline[0]) in [1,2,3,4,5,6,7,8,9,10]: # TODO:
                    print("TODO: Skipping hardware_bin_descriptions instance: [%d] %s"%(ln,line))
                    continue 
                raise RuntimeError("Unsupported line in hardware_bin_descriptions: [%d] %s"%(ln,line)) 
            

            if tf_section: 
                if RE_END.search(line): tf_lines['end']=ln-1;tf_section=False;continue 
                else: continue 
            if info_section: 
                if RE_END.search(line): info_section=False;continue 
                match = RE_INFO_DESC.search(line)
                if match: obj.info.description = match.group("item"); continue
                match = RE_INFO_DEV_NAME.search(line)
                if match: obj.info.device_name = match.group("item"); continue 
                match = RE_INFO_DEV_REV.search(line)
                if match: obj.info.device_revision = match.group("item"); continue 
                match = RE_TEST_REVISION.search(line)
                if match: obj.info.test_revision = match.group("item");continue 
                raise RuntimeError("Unsupported line in information: [%d] %s"%(ln,line)) 
            if decl_section: 
                if RE_END.search(line): decl_section=False;continue 
                match = RE_DECL_TF_VAR.search(line)
                if match: obj.decl.add_var(match.group("var"),match.group("val").strip()); continue  
                raise RuntimeError("Unsupported line in declarations: [%d] %s"%(ln,line)) 
            if impl_decl_section: 
                if RE_END.search(line): impl_decl_section=False;continue 
                raise RuntimeError("Unsupported line in implicit_declarations: [%d] %s"%(ln,line)) 
            if flags_section: 
                if RE_END.search(line): flags_section=False;continue 
                match = RE_FLAG.search(line)
                if match: obj.flags.add(Flag(user=False,name=match.group("name").strip(),val=match.group("val").strip())); continue 
                match = RE_USER_FLAG.search(line)
                if match: obj.flags.add(Flag(user=True,name=match.group("name").strip(),val=match.group("val").strip())); continue 
                raise RuntimeError("Unsupported line in flags: [%d] %s"%(ln,line)) 
            if tm_params_section: 
                if RE_END.search(line): tm_params_section=False;continue 
                match = RE_TM_NUM.search(line)
                if match: tmnum=match.group("tmnum").strip();obj.tms.add(tmnum);continue 
                match = RE_STR_STR.search(line)
                if match: obj.tms[tmnum].add_param(match.group("lhs").strip(),match.group("rhs").strip()); continue 
                raise RuntimeError("Unsupported line in testmethodparameters: [%d] %s"%(ln,line)) 
            if tm_limits_section: 
                if RE_END.search(line): tm_limits_section=False;continue 
                match = RE_TM_NUM.search(line)
                if match: tmnum=match.group("tmnum").strip();obj.tms.add(tmnum);continue 
                match = RE_TM_LIMIT.search(line)
                if match: obj.tms[tmnum].add_limit(*match.groups()); continue 
                raise RuntimeError("Unsupported line in testmethodlimits: [%d] %s"%(ln,line)) 
            if tms_section: 
                if RE_END.search(line): tms_section=False;continue 
                match = RE_TM_NUM.search(line)
                if match: tmnum=match.group("tmnum").strip();obj.tms.add(tmnum);continue 
                match = RE_TM_NAME.search(line)
                if match: obj.tms[tmnum].add_name(match.group("name")); continue 
                raise RuntimeError("Unsupported line in testmethods: [%d] %s"%(ln,line)) 
            if ts_section: 
                if RE_END.search(line): ts_section=False;continue 
                match = RE_TS_NAME.search(line)
                if match: tsname = match.group("name"); obj.tss.add(TestSuite(name=tsname,settings={}));continue 
                match = RE_TS_SETTING.search(line)
                if match: obj.tss[tsname].add_setting(*match.groups()); continue 
                raise RuntimeError("Unsupported line in testsuites: [%d] %s"%(ln,line)) 
            if binning_section: 
                if RE_END.search(line): binning_section=False;continue 
                match = RE_OW_BIN.search(line)
                if match: print("WARNING: (%s): Skipping instance of 'otherwise bin': [%d] %s"%(func,ln,line)); continue
                if line.startswith("\""): print("TODO: Skipping Bin defines in binning."); continue 
                raise RuntimeError("Unsupported line in binning: [%d] %s"%(ln,line)) 
            if context_section: 
                if RE_END.search(line): context_section=False;continue 
                match = RE_TIMING.search(line)
                if match: obj.timing = match.group("file").strip();continue 
                match = RE_LEVELS.search(line)
                if match: obj.levels = match.group("file").strip();continue 
                match = RE_CONFIG.search(line)
                if match: obj.config = match.group("file").strip();continue
                match = RE_VECTOR.search(line)
                if match: obj.vector = match.group("file").strip();continue 
                match = RE_CHN_ATTR.search(line)
                if match: obj.channel_attribute= match.group("file").strip();continue
                raise RuntimeError("Unsupported line in context: [%d] %s"%(ln,line)) 
            # FREELANCE: 
            if RE_TEST_FLOW.search(line):    tf_section=True;tf_lines['start']=ln-1;continue  
            if RE_INFORMATION.search(line):  info_section=True; continue 
            if RE_DECLARATIONS.search(line): decl_section=True;continue 
            if RE_IMPL_DECL.search(line):    impl_decl_section=True;continue 
            if RE_FLAGS.search(line):        flags_section=True;continue 
            if RE_TM_PARAMS.search(line):    tm_params_section=True;continue 
            if RE_TM_LIMITS.search(line):    tm_limits_section=True;continue 
            if RE_TMS.search(line):          tms_section=True;continue 
            if RE_TSS.search(line):          ts_section=True;continue 
            if RE_BINNING.search(line):      binning_section=True;continue 
            if RE_CONTEXT.search(line):      context_section=True;continue 
            if RE_HW_BIN_DESC.search(line):  hw_bin_desc_section = True; continue 

            if RE_BIN_DISCONT.search(line):  
                bin_disconnect_section=True; 
                tsname= "bin_disconnect"
                obj.tss.add(TestSuite(name=tsname,special=True,settings={})) 
                continue 
            if RE_MULTI_BIN_DEC.search(line): 
                multi_bin_decision_section = True
                tsname = "multi_bin_decision"
                obj.tss.add(TestSuite(name=tsname,special=True,settings={})) 
                continue
         

            if RE_TF_HEADER.search(line):    continue  # NOTE: Not need to store (?)
            if RE_TF_LANG_REV.search(line):  continue  # NOTE: Not need to store (?)
            raise RuntimeError("Unsupported line: [%d] %s"%(ln,line)) 

    print("DEBUG: (%s): Initial pass complete. Moving to testsuite limits and parameter settings..."%(func))
    for ts in obj.tss: 
        ts.tm     = obj.get_tm_name(ts.name)
        ts.params = obj.get_tm_params(ts.name)
        ts.limits = obj.get_tm_limits(ts.name)


    ## Second pass over the test_flow structure 
    # The reason for havinga second pass on the Testflow file structure 
    # is to no link the module with a 'bad' pasring method. If I separate
    # and solidify the strucutre, then someone else can come in and rewrite
    # the structure.
    print("testflow structure: ",tf_lines)

    # Line-by-line processing
    i = tf_lines["start"]; iend = tf_lines["end"]
    #while i <= iend: 
    #    print(lines[i])
    #    i+=1  


    print("WARNING: Skipping testflow structure processing.")
    return obj 

    ## Full string processing
    ## ----------------------
    special_chars = ["{","}","(",")",",",";","!","=","@",'.','-','+',"<",">"] 
    space_chars   = [" ","\n","\t"]
    lower  = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] 
    upper  = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    number = ['0','1','2','3','4','5','6','7','8','9']
    alphanumeric = lower + upper + number + ['_'] 
    re_digits = re.compile("^\d+$")
    keywords = ["groupbypass","open","closed","if","else","then","or","and",
                "run_and_branch","run",
                
                "stop_bin"]


    RE_CLOSED_GRP = re.compile("closed\s*,\s*\"(?P<name1>.*)\"\s*,\s*\"(?P<name2>.*)\"")
    RE_OPEN_GRP   = re.compile("open\s*,\s*\"(?P<name1>.*)\"\s*,\s*\"(?P<name2>.*)\"")

    RE_RUN_AND_BRANCH = re.compile("run_and_branch\((?P<name>\w+)\)")



    def stringify_tokens(tokens,start,stop): 
        
        i = start; iend = stop   
        retstr = []
        while i <= iend: 
            retstr.append(tokens[i]['token'])
            i+=1
        return "".join(retstr)

    def classify_token(token): 
        if token in keywords: return token
        if re_digits.search(token): return 'digits'
        return 'identifier'



    string = "\n".join(lines[tf_lines["start"]:tf_lines["end"]])
    ln = int(tf_lines['start']); 
    charOnLineIndex = 1
    lastchar = ''
    nextchar =''
    inputLength = len(string) - 1

    tokens = []; token = []
    sytbl = {
        "run_and_branch" : [],
        "run" : [],
        "ocb" : [],
        "ccb" : [],
        "cb-sets": OrderedDict(),
        "semicolon": []
    }
    last_ocb = []
    cbs = 0

    in_str_literal = False 
    char_handled   = False

    for i, char in enumerate(string): 
        if debug: print("DEBUG: [%s]: %s"%(i,char))
        # Infastructure for lookahead: 
        if i == inputLength: nextchar = ''
        else: nextchar = string[i+1]
        # Infastructure for reporting: 
        if char == '\n': 
            ln += 1
            charOnLineIndex = 1
        else: charOnLineIndex += 1

        # States Seciton: 
        # ---------------
        if in_str_literal: 
            if char == '\"' and lastchar != '\\': # TODO: I dont think '//' is needed
                if debug: print('DEBUG:  - closing string-literal state')
                in_str_literal = False; 
                token.append(char) # NOTE: We are keeping the double quotes. 
                _token = "".join(token)
                if _token:
                    tokens.append({'token':_token, 'tag':'identifier'})
                    token = []
                else: print("WARNING: Empty double qoutes found.")
            else: token.append(char)
            lastchar = char; continue;    

        # Freelance section: 
        # ------------------          
        if char == '\"':  # Catch string-literals...
            if debug: print('DEBUG: (%s): - setting string-literal state'%(func))
            in_str_literal = True
            token.append(char) # NOTE: We are keeping the double quotes. 
            lastchar = char; continue; 

        if char in space_chars: 
            if lastchar in space_chars: # chained spaces
                lastchar = char; continue; 
            if token:
                if debug: print("DEBUG: - pushing token on space, %s"%("".join(token)))     
                _token = "".join(token)
                if _token:
                    tag = classify_token(_token)
                    tokens.append({'token':_token, 'tag':tag})
                    if tag == "run_and_branch":
                        sytbl['run_and_branch'].append(len(tokens)-1)
                    elif tag == "run": 
                        sytbl['run'].append(len(tokens)-1)
                    token = []
            else: lastchar = char; continue;            

        elif char in special_chars: 
            _token = "".join(token)
            if _token: 
                tag = classify_token(_token)
                tokens.append({'token':_token,'tag':tag})
                token = []
                if tag == "run_and_branch":
                    sytbl['run_and_branch'].append(len(tokens)-1)
                elif tag == "run": 
                    sytbl['run'].append(len(tokens)-1)
            tokens.append({'token':char,'tag':char})

            if char == "{": 
                cbs += 1
                sytbl['ocb'].append(len(tokens)-1)
                last_ocb.append(len(tokens)-1)
                
            elif char == "}": 
                cbs -= 1
                sytbl['ccb'].append(len(tokens)-1)
                #sytbl['cb-sets'].append([last_ocb.pop(),sytbl['ccb'][-1]])
                sytbl['cb-sets'][last_ocb.pop()] = sytbl['ccb'][-1]

            elif char == ";": 
                sytbl['semicolon'].append(char)
            
            continue 
      
        elif char in alphanumeric: 
            token.append(char)
        else: 
            raise RuntimeError("BAd char: %s, token = %s, ln = %s"%(char,token,ln))

    ## build 
    for i in sytbl['run_and_branch']: 
        #print("run_and_branch",i,tokens[i])
        pass 

    breakval = 40000

    grps = []
    tss  = OrderedDict()
    grp_range = [] # [start,stop] or the latest group 

    flow = Flow(tokens = tokens) 

    i = 0; iend = len(tokens) - 1
    while i <= iend: 
        token = tokens[i]['token']
        tag   = tokens[i]['tag']
        #print(i,token,tag)

        if i == 0: 
            if token != 'test_flow': 
                raise RuntimeError("First token should be 'test_flow'")
            i+=1; continue 
        
        
        if token == "{": 
            #print(token,i,sytbl['cb-sets'][i])
            ccb = sytbl['cb-sets'][i]
            if tokens[ccb+2]['token'] == "groupbypass": 
                tstr = stringify_tokens(tokens,ccb+1,ccb+1+7) 
                closed = RE_CLOSED_GRP.search(tstr)
                opened = RE_OPEN_GRP.search(tstr)
                if closed: grpname = closed.group("name1")
                elif opened: grpname = opened.group("name1")
                else: raise RuntimeError("Group has bad form: %s"%(tstr))
                print("DEBUG: GROUP(byp):  %s"%(name))
                grps.append({'name':grpname,"start":i,"stop":ccb})
                grp = flow.add_group(Group(grpname,status=status,start=i,stop=ccb))
                grp_range = [i,ccb]
            if tokens[ccb+2]['token'] in ["closed",'open']: 
                tstr = stringify_tokens(tokens,ccb+1,ccb+1+5)
                closed = RE_CLOSED_GRP.search(tstr)
                opened = RE_OPEN_GRP.search(tstr)
                if closed: grpname = closed.group("name1"); status = 'closed'
                elif opened: grpname = opened.group("name1"); status = 'open'
                else: raise RuntimeError("Group has bad form: %s"%(tstr))
                print("DEBUG: GROUP: %s"%(grpname))
                grps.append({'name':grpname,"start":i,"stop":ccb})
                grp = flow.add_group(Group(grpname,status=status,start=i,stop=ccb))
                grp_range = [i,ccb]
 
        if token == "run_and_branch": 
            tstr = stringify_tokens(tokens,i,i+3)
            match = RE_RUN_AND_BRANCH.search(tstr)
            if match: 
                tsname = match.group('name')                
                if tsname in tss: raise RuntimeError("Double ts instance: %s"%(tsname))
                else: tss[tsname] = i + 2
                print("DEBUG: TESTSUITE: %s"%(tsname))
                if grp_range: 
                    if i > grp_range[0] and i < grp_range[1]: 
                        node = flow.add_node(Node(name=tsname,index=i+2),grp.name)
                    else: node = flow.add_node(Node(name=tsname,index=i+2))
                else: node = flow.add_node(Node(name=tsname,index=i+2))


                #sys.exit(1)


            else:
                raise RuntimeError("Run-and-branch bad form: %s"%(tstr))
        
        #if i == breakval: break
        i +=1

    print("i",i)
    for i,grp in enumerate(grps,start=1): 
        print("%-3d.) %-30s, start = %-6s, stop = %-6s "%(i,grp['name'],grp['start'],grp['stop']))

    for ts,i in tss.items(): 
        print("%-90s, %s"%(ts,i)) 
    return obj
             

# ----------------------------------------------------------------------------: 
class Bin(object): 
    def __init__(self,name,num,bintype,color,over_on=False): 
        self.name = name 
        self.num  = num 
        self.bintype = bintype 
        self.color = color 
        self.over_on = over_on
class Bins(st7putils.Container): 
    def __init__(self, ): 
        super(Bins,self).__init__()
    def add(self,binn): 
        super(Bins,self).add(binn,Bin)
# ----------------------------------------------------------------------------: 

# ----------------------------------------------------------------------------: 
# If Group and Node (and Bin) are to know their token placements then maybe 
# the Flow class should be the one creating them.  
class Flow(object): 
    def __init__(self,tokens):
        """ 
          tokens : list of dictionaries
           this parameter should be built during the read method.  
        """
        self.tokens = tokens 
    
        self.groups = Groups()
        self.nodes  = Nodes() 
        self._ids   = 0 
   
    def add_group(self, group): 
        self._ids += 1
        group.set_id(self._ids)
        self.groups.add(group)
        return self.groups.__last__()


    def add_node(self,node,grp=None): 
        self._ids += 1
        node.set_id(self._ids)
        self.nodes.add(node)
        if grp: self.groups[grp].nodes.append(self._ids)
        return self.nodes.__last__()
        
  


class Groups(st7putils.Container): 
    def __init__(self, ): 
        super(Groups,self).__init__()
    def add(self,group): 
        super(Groups,self).add(group,Group)

class Group(object): 
    def __init__(self,name,status,start,stop): 
        self.name   = name 
        self.status = status # open / closed
        self.start  = start   # start token 
        self.stop   = stop     # stop token 
        self._id    = -1 

        self.nodes = []
   
    def set_id(self,ID): 
        self._id = ID


class Nodes(st7putils.Container): 
    def __init__(self, ): 
        super(Nodes,self).__init__()
    def add(self,node): 
        super(Nodes,self).add(node,Node)

class Node(object): 
    def __init__(self,name,index): 
        self.name = name 
        self.index = index
        self.pass_ptr = None # Pointers to Nodes, Bins, etc... 
        self.fail_ptr = None 
        self._id    = -1 
    def set_id(self,ID): 
        self._id = ID
# ----------------------------------------------------------------------------: 



class Info(object): 
    def __init__(self,): 
        self.description = ""
        self.device_name = ""
        self.device_revision = ""
        self.test_revision = ""
 
class Decl(object): 
    def __init__(self): 
        self.vars = {}
    def add_var(self,var,val): 
        if var in self.vars: raise RuntimeError("Var already declared: %s"%(var))
        self.vars[var] = val

class Flag(object): 
    def __init__(self,name,val,user): 
        self.name = name; self.val = val; self.user=user

class Flags(st7putils.Container): 
    def __init__(self, ): 
        super(Flags,self).__init__()
    def add(self,flag): 
        super(Flags,self).add(flag,Flag)



# ----------------------------------------------------------------------------:
# NOTE: There seems to be a terminology discrepancy between the 'binning' section
# within the testflow file (43086) and the Smt7 'Bins' page (99267). 
class Bin(object): 
    def __init__(self,hw_num = -1, hw_desc = "",
                      sw_num = -1, sw_desc = "", 
                      fail_bin = -1, reprobe = -1, 
                      overon = -1, ow_bin = -1):
        self.hw_num   = hw_num 
        self.hw_desc  = hw_desc
        self.sw_num   = sw_num 
        self.sw_desc  = sw_desc
        self.fail_bin = fail    # 0 = Not, 1 = Is
        self.reprobe  = reprobe # 0 = Not, 1 = Is.
        self.overon   = overon  # 0 = Not, 1 = Is
        self.ow_bin   = ow_bin  # 0 = Not, 1 = Is. 
class Bins(st7putils.Container): 
    def __init__(self, ): 
        super(Bins,self).__init__()
    def add(self,bin): 
        super(Bins,self).add(bin,Bin)
# ----------------------------------------------------------------------------:

class TestMethod(object): 
    def __init__(self,num,name="",params={},limits={}): 
        self.num = num
        self.name = name  
        self.params = params
        self.limits = limits


    def add_name(self, name): self.name =name 
    def add_param(self,param,val): 
        if param in self.params: 
            raise RuntimeError("'%s' param '%s' is already declared."%(self.num,param))
        self.params[param] = val

    def add_limit(self,var, lv, lvcs, hv, hvcs, unit, offset, incr):
        self.limits[var] = {"low-value":lv,"low-value-compr-sys":lvcs,
                            "high-value":hv,"high-value-compr-sys":hvcs,
                            "unit": unit, "test-num_offset":offset, 
                            "test-num-incr":incr}
        return 

    def __str__(self): 
        return "%s: params=%s"%(self.num,self.params)

class TestMethods(object): 
    def __init__(self): 
        self.objects = OrderedDict() # tm-num->object
        self.__tmNumMap = {} # tm-num -> tm-name


    def get_tm_num_map(self): 
        if self.__tmNumMap: return self.__tmNumMap
        for tmNum, tmObj in self.objects.items(): 
            if tmNum in self.__tmNumMap: 
                raise RuntimeError("Double instance of tm-num %s in internal map"%(tmNum))
            self.__tmNumMap[tmNum] = tmObj.name
        return self.__tmNumMap

    def add(self,num):
        if num in self.objects: pass 
        else:  self.objects[num] = TestMethod(num,name="",limits={},params={})

    def __contains__(self, num): 
        if num not in self.objects.keys(): return False 
        else: return True

    def names(self):
        names = set()
        for num in self.objects: set.add(self.objects[num].name)
        names = set([self.objects[num] for num in self.objects])
        return names

    def length(self): 
        return len(self.objects)
   
    def __len__(self): 
        return len(self.objects)
 
    def __getitem__(self, num): 
        return self.objects[num]

    def __iter__(self): 
        for num in self.objects.keys(): 
            yield self.objects[num]

    def __last__(self): 
        return self.objects[next(reversed(self.objects))]    

    def __str__(self): 
        rs = []
        for i,num in enumerate(self.objects,start=1): 
            rs.append(str(i) + str(self.objects[num]))
        return "\n".join(rs)
        
# ----------------------------------------------------------------------------:
class TestSuite(object): 
    def __init__(self, name, special=False, settings={}): 
        self.name = name 
        self.settings = settings 
        self.special = special
        self.tm     = None # NOTE: Set during second pass w/in read method
        self.limits = None # NOTE: Set during second pass w/in read method
        self.params = None # NOTE: Set during second pass w/in read method

    def add_setting(self,setting,val): 
        if setting in self.settings: 
            raise RuntimeError("Testsuite '%s' setting '%s' is already declared."%(self.name,setting))
        self.settings[setting] = val

    def is_bypassed(self,): 
        """Return boolean representing if testsuite is bypassed"""
        if "local_flags" in self.settings.keys(): 
            if "bypass" in self.settings["local_flags"]: 
                return True
        # TODO: check if bypassed within the groups
        return False 


    def get_tm_num(self):
        """ 
        This function returns the test-method number set to the test-suites
        'override_testf' setting. To get the full-proper name of the 
         test-method, please use the Testflow's method function 
        'get_test_method'. 
        """
        if "override_testf" not in self.settings: return ""
        return self.settings["override_testf"].strip("\" ")


    def get_label(self): 
        """
        Return the sequencer label. If no
        If sequencer label, return an empty string.
        """
        if "override_seqlbl" not in self.settings: return ""
        return self.settings["override_seqlbl"].strip("\"") 

    # ------------------------------------------------------------------------:
    # Levels
    def get_lvl_eqnset(self):
        """ Returns the integer pointer with the EQNSET."""
        if "override_lev_equ_set" not in self.settings: return ""
        return int(self.settings["override_lev_equ_set"])

    def get_lvl_specset(self): 
        """ Returns the integer pointer with the SPECSET."""
        if "override_lev_spec_set" not in self.settings: return ""
        return int(self.settings["override_lev_spec_set"])

    def get_lvl_lvlset(self): 
        """ Returns the integer pointer with the LEVELSET within the EQNSET."""
        if "override_levset" not in self.settings: return ""
        return int(self.settings["override_levset"])

    def get_lvl_settings(self,): 
        """ 
        Returns the level setting. It is a simple concatenation of the 
        following methods: `TestSuite.get_lvl_eqnset`, 
        `TestSuite.get_lvl_specset`, `TestSuite.get_lvl_lvlset`. 

        Therefore, the string is '<eqnset>,<specset>,<levelset>'
        """
        return ",".join([str(self.get_lvl_eqnset()),str(self.get_lvl_specset()),str(self.get_lvl_lvlset())])
    # ------------------------------------------------------------------------:
    
    # ------------------------------------------------------------------------:
    # Timing related queries: 
    # 
    def get_tim_timset(self):
        """ 
        Returns a list of the integer pointers. This function always returns 
        a list in order to support single-port and multi-port timing. 
        """
        if "override_timset" not in self.settings: return ""
        timset = self.settings["override_timset"]
        try: 
            timset = [int(timset)]
        except: 
            timset = [ int(x) for x in timset.strip('\"').split(",")]
        return timset 

    def get_tim_eqnset(self): 
        if "override_tim_equ_set" not in self.settings: return ""
        return self.settings["override_tim_equ_set"]

    def get_tim_specset(self): 
        if "override_tim_spec_set" not in self.settings: return ""
        return self.settings["override_tim_spec_set"]

    def is_multiport_timing(self):
        """ 
        Returns a boolean. 
        """
        # TODO: This can be improved to analyze the eqnset value
        specset = self.get_tim_specset()
        if not specset: return False
        if specset.isdigit(): return False 
        else: return True

    def get_tim_settings(self,):
        """ 
        Returns the timing settings.

        If the timing is a multiport setup, then the specification 
        name is returned. 

        if the imitng is a single-port setup, then a simple 
        concatenation of the following methods: `TestSuite.get_tim_eqnset`, 
        `TestSuite.get_tim_specset`, `TestSuite.get_tim_timset`, is returned.
         Therefore, the string is '<eqnset>,<specset>,<levelset>'
        """
        if self.is_multiport_timing(): 
            return self.get_tim_specset() 
        return ",".join([str(self.get_tim_eqnset()),str(self.get_tim_specset()),str(self.get_tim_timset())])
    # ------------------------------------------------------------------------:

    def tm_num(self): 
        """Return the test method number."""
        if "override_testf" not in  self.settings.keys(): return ""
        return self.settings["override_testf"] 
    
    def flags(self): # TODO
        """Return the local flags."""
        return "TODO:FLAGS"

class TestSuites(st7putils.Container): 
    def __init__(self): 
        super(TestSuites,self).__init__()
        self._uniqlbls = {} # lbl -> [tss]

    def add(self, testsuite):
        super(TestSuites,self).add(testsuite,TestSuite)


    def get_unique_single_port_timings(self, ):
        """ 
        Returns a dictionary of all unique single port timing 
        setups referenced throughout the testflow. 

        The keys are the unique timing setups and the values are lists 
        of testsuites using said timings.
        """
        unique_timings = {} 
        for tsname,ts in self.objects.items(): 
             if ts.is_multiport_timing(): continue 
             tm = ts.get_tim_settings() 
             #print(ts.name,ls)
             if tm in unique_timings: 
                 unique_timings[tm].append(tsname)
             else: 
                 unique_timings[tm] = [tsname]
        return unique_timings

    def get_unique_multi_port_timings(self, ):
        """ 
        Returns a dictionary of all unique multi-port timing 
        setups referenced throughout the testflow. 

        The keys are the unique timing setups and the values are lists 
        of testsuites using said timings.
        """
        unique_timings = {} 
        for tsname,ts in self.objects.items(): 
             if not ts.is_multiport_timing(): continue 
             tm = ts.get_tim_settings() 
             #print(ts.name,ls)
             if tm in unique_timings: 
                 unique_timings[tm].append(tsname)
             else: 
                 unique_timings[tm] = [tsname]
        return unique_timings

    def get_unique_lvls(self, countBypassed=True): 
        """ 
        Returns a dictionary of all unique level setups referenced
        throughout the testflow. 

        The keys are the unique level setups and the values are lists 
        of testsuites using said levels.
        """
        unique_lvls = {} 

        for tsname,ts in self.objects.items(): 
             ls = ts.get_lvl_settings() 
             #print(ts.name,ls)
             if ls in unique_lvls: 
                 unique_lvls[ls].append(tsname)
             else: 
                 unique_lvls[ls] = [tsname]
        return unique_lvls
         
    def get_unique_tms(self, tmMap): 
        """ 
        Returns a dictionary of all unique test methods referenced
        throughout the testflow. 

        The keys are the unique testmethods and the values are lists 
        of testsuites using said label.

        Parameters: 
          tmMap : dictionary
            key is tm-number and value is tm-name. This typically 
            will be coming from the `st7p.testflow.Testflow` class.   
        """
        unique_tms = {} 
        for tsname,ts in self.objects.items(): 
            _tmNum = ts.get_tm_num()

            #print("DEBUG",tsname,_tmNum)
            if not _tmNum: continue 
            if _tmNum not in tmMap:
                raise RuntimeError("Missing tm-num %s from internal map"%(_tmNum))
            if tmMap[_tmNum] in unique_tms: 
                unique_tms[tmMap[_tmNum]].append(tsname)
            else: 
                unique_tms[tmMap[_tmNum]] = [tsname]
        return unique_tms
      

    def get_unique_labels(self, countBypassed=True): 
        """
        Returns a dictionary of all unique labels referenced throughout 
        the testflow.  

        The keys are the unique labels and the values are lists 
        of testsuites using said label. 

        Parameters: 
          countBypassed : bool, default = True
            If true, bypassed testsuites will be accounted for. 
            Otherwise, they will be ignored. 
        """
        #if self._uniqlbls: return self._uniqlbls
        # ^^^ Because we allow parameters to change the search, we cant
        # store the last search . 
        uniqlbls = {} 
        for tsname, ts in self.objects.items():
            if "override_seqlbl" not in  ts.settings.keys(): continue 
            if ts.is_bypassed()  and not countBypassed: continue  
            # TODO: check if bypassed within the groups
            lbl = ts.settings["override_seqlbl"].strip("\"")
            if lbl in uniqlbls: uniqlbls[lbl].append(tsname)
            else: uniqlbls[lbl] = [tsname] 
        return uniqlbls


class Testflow(object): 
    def __init__(self,sfp="",debug=False): 
        self._debug = debug
        if sfp:  self._abs_path, self._dd_path, self._filename = st7putils._93k_file_handler(sfp, "testflow")
        else:    self._abs_path = ""; self._dd_path = ""; self._filename = ""; 
        self.info   = Info()
        self.decl   = Decl()
        self.flags  = Flags()
        self.tms    = TestMethods()
        self.tss    = TestSuites()
        self.bins   = Bins() 
        self.timing = ""
        self.levels = ""
        self.config = ""
        self.vector = ""
        self.channel_attribute = ""
        #self.flow = Flow() # TODO

    def get_test_method(self,ts): 
        if isinstance(ts,str): 
            ts = self.tss[ts]
        return self.tms[ts.get_test_method()].name

    # Test method: -----------------------------------------------------------:
    def get_tm_name(self,ts): 
        if isinstance(ts,str): 
            ts = self.tss[ts]
        return self.tms[ts.get_tm_num()].name

    def get_tm_params(self,ts): 
        if isinstance(ts,str): 
            ts = self.tss[ts]
        return self.tms[ts.get_tm_num()].params

    def get_tm_limits(self,ts): 
        if isinstance(ts,str): 
            ts = self.tss[ts]
        return self.tms[ts.get_tm_num()].limits
    # ------------------------------------------------------------------------: 
        
        


    def get_dd_path(self):  return self._dd_path
    def get_abs_path(self): return self._abs_path

    def get_unique_lvls(self,countBypassed=True): 
        """
        Calls `TestSuites.get_unique_lvl` method.  

        Returns a dictionary of all unique level setups referenced throughout 
        the testflow.  

        The keys are the unique level setups and the values are lists 
        of testsuites using said level setups

        Parameters: 
          countBypassed : bool, default = True
            If true, bypassed testsuites will be accounted for. 
            Otherwise, they will be ignored. 
        """
        return self.tss.get_unique_lvls(countBypassed=countBypassed)

    def get_unique_labels(self,countBypassed=True): 
        """
        Calls `TestSuites.get_unique_labels` method.  

        Returns a dictionary of all unique labels referenced throughout 
        the testflow.  

        The keys are the unique labels and the values are lists 
        of testsuites using said label. 

        Parameters: 
          countBypassed : bool, default = True
            If true, bypassed testsuites will be accounted for. 
            Otherwise, they will be ignored. 
        """
        return self.tss.get_unique_labels(countBypassed=countBypassed)

    def get_unique_tms(self,):
        """ 
        Calls `TestSuites.get_unique_tms` method.  

        NOTE: A similiar info could be obtained via the `TestMethods`
        class. However, it would be more difficult to obatin the 
        test-suite's that reference each test-method. 
        """
        return self.tss.get_unique_tms(self.tms.get_tm_num_map()) 

    def get_unique_single_port_timings(self, ): 
        return self.tss.get_unique_single_port_timings() 

    def get_unique_multi_port_timings(self, ): 
        return self.tss.get_unique_multi_port_timings() 

    def get_config_path(self): 
        if not self.config: return ""
        return os.path.join(self._dd_path,"configuration",self.config)

    def get_levels_path(self): 
        if not self.levels: return ""
        return os.path.join(self._dd_path,"levels",self.levels)

    def get_timing_path(self): 
        if not self.timing: return ""
        return os.path.join(self._dd_path,"timing",self.timing)

    def get_vectors_path(self): 
        if not self.vector: return ""
        return os.path.join(self._dd_path,"vectors",self.vector)

    def get_channel_attribute_path(self): 
        if not self.channel_attribute: return ""
        return os.path.join(self._dd_path,"ch_attributes",self.channel_attribute)

    def summary(self,mask=False): 
        """ 
        Report high-level information related to the Testflow object.
        Parameter: 
          mask : bool, default = False
            If true, the source file path will be masked from reporting.
        """
        func = "st7p.testflow.summary"
        print("\n" + "-"*(func.__len__()+2) + ":")
        print(""+func + "  :");print("-"*(func.__len__()+2) + ":")
        if mask: print("[%s]: Source-path: %s"%(func, "<masked>"))
        else:    print("[%s]: Source-path: %s"%(func, self._abs_path))
        print("[%s]: Number of testsuites: %s"%(func, self.tss.length()))
        print("[%s]: Number of unique labels: %s"%(
                     func, self.get_unique_labels().__len__()))
        print("[%s]: Number of unique testmethods: %s"%(
                     func, self.get_unique_tms().__len__()))
        print("[%s]: Number of unique levels setups: %s"%(
                     func, self.get_unique_lvls().__len__()))
        print("[%s]: Number of unique single-port timing setups: %s"%(
                     func, self.get_unique_single_port_timings().__len__()))
        print("[%s]: Number of unique multi-port timing setups: %s"%(
                     func, self.get_unique_multi_port_timings().__len__()))
        return 
   

# ----------------------------------------------------------------------------:
def __handle_cmdline_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", 
                        help="Increase console logging", 
                        action="store_true")
    parser.add_argument("testflow", help="Testflow file path")
    args = parser.parse_args()
    if not os.path.isfile(args.testflow): 
        raise ValueError("Invalid file")
    return args
# ----------------------------------------------------------------------------:
if __name__ == "__main__": 
    args = __handle_cmdline_args()
    obj = read(sfp = args.testflow, debug = args.debug)

    print("")
    print("Info-block:")
    print("  - obj.info.description: %s"%(obj.info.description))
    print("  - obj.info.device_name: %s"%(obj.info.device_name))
    print("  - obj.info.device_revision: %s"%(obj.info.device_revision))
    print("  - obj.info.test_revision: %s"%(obj.info.test_revision))
    print("")
   
    print("Declarations-block")
    print("  - len(obj.decl.vars): %s  // Number of testflow variables defined."%(len(obj.decl.vars)))
    print("")
   
    print("Flags-block:")
    print("  - len(obj.flags): %s  // Number of flags defined (system and user)."%(len(obj.flags)))
    print("")
    
    print("Context-block:")
    print("  - obj.config: %s"%(obj.config))
    print("  - obj.levels: %s"%(obj.levels))
    print("  - obj.timing: %s"%(obj.timing))
    print("  - obj.vector: %s"%(obj.vector))
    print("  - obj.channel_attribute: %s"%(obj.channel_attribute))
    print("")

    print("\nNOTE: If in interactive mode, use variable name 'obj' to"\
          " the parsed object.")
