#!/home/utils/Python-2.7.13/bin/python
import sys, os, re, argparse
import st7p.testflow
import st7p.timing
import st7p.levels
import st7p.config
import st7p.vectors
import st7p.st7putils as st7putils  
from collections import OrderedDict
# TODO: How many unique labels processed? 
# TODO: Total size of pattern parsed. 
# TODO: Execution time? 
# 
# ----------------------------------------------------------------------------:
def _handle_cmd_line_args(): 
    func = "_handle_cmd_line_args"
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true",
                        help="increase output verbosity.")
    parser.add_argument("testflow",metavar="testflow",type=str,
                        help="testflow file to be proces")
    parser.add_argument("--bbn_csv",
                        help="BBN HPU temp data: idx[ms],ts,temp")
    args = parser.parse_args()
    if not os.path.isfile(args.testflow): 
        raise RuntimeError("Testflow doesn't exist or has bad permissions.")
    if args.bbn_csv: 
        if not os.path.isfile(args.bbn_csv): 
            raise RuntimeError("BBN-CSV doesn't exist or has bad permissions.")
    return args
# ----------------------------------------------------------------------------:
def read_out_values(row):
    new_row = []
    new_row.append(row['test-suite'])
    new_row.append(str(row['temp-1']))
    for supply in cfo.supplies: 
        new_row.append(str(row["%s-vout"%(supply.name)]))
        new_row.append(str(row["%s-ilimit-source"%(supply.name)]))
        new_row.append(str(row["%s-ilimit-sink"%(supply.name)]))
    for pin in cfo.pins: 
        new_row.append(str(row["%s-vih"%(pin.name)]))
        new_row.append(str(row["%s-vil"%(pin.name)]))
        new_row.append(str(row["%s-voh"%(pin.name)]))
        new_row.append(str(row["%s-vol"%(pin.name)]))
        new_row.append(str(row["%s-period"%(pin.name)]))
        new_row.append(str(row["%s-vectors"%(pin.name)]))
        new_row.append(str(row["%s-cycles"%(pin.name)]))
        new_row.append(str(row["%s-num-of-labels"%(pin.name)]))
    #new_row.append(str(row['temp-2']))
    #new_row.append(str(row['temp-3']))
    return new_row


def error_log(setup_ref,err_msg,err_list=[]): 
    print("ERROR: %s"%(err_msg))
    print("ERROR: Log Setup Reference")
    print("ERROR: Device   : %s"%(setup_ref['dev']))
    print("ERROR: Testflow : %s"%(setup_ref['testflow']))
    print("ERROR: Config   : %s"%(setup_ref['config']))
    print("ERROR: Levels   : %s"%(setup_ref['levels']))
    print("ERROR: Timing   : %s"%(setup_ref['levels']))
    print("ERROR: PMF      : %s"%(setup_ref['pmf']))
    print("ERROR: -> testsuite : %s"%(setup_ref['testsuite']))
    print("ERROR: -> label     : %s"%(setup_ref['label']))
    if err_list.__len__() >= 1:
        for item in err_list:
            print("ERROR list-item: %s"%(item)) 
    raise RuntimeError(err_msg)

if __name__ == "__main__": 
    args = _handle_cmd_line_args()
    tfo = st7p.testflow.read(args.testflow,debug=args.debug)
    cfo = st7p.config.read(tfo.get_config_path())
    lvo = st7p.levels.read(tfo.get_levels_path())
    tmo = st7p.timing.read(tfo.get_timing_path())
    pmf = st7p.vectors.read(tfo.get_vectors_path())

    print("\n------------:")
    print("Setup files :")
    print("------------:")
    print("Device path : %s"%(tfo._dd_path))
    print("Testflow    : %s"%(tfo._abs_path))
    print("Config file : %s"%(cfo._abs_path))
    print("Levels file : %s"%(lvo._abs_path))
    print("Timing file : %s"%(tmo._abs_path))
    print("PMF         : %s"%(pmf._abs_path)) 
    dd_path = tfo._dd_path 
    setup_reference = {"dev":tfo._dd_path, 
                      "testflow":tfo._abs_path,
                      "config":cfo._abs_path, 
                      "levels":lvo._abs_path,
                      "timing":tmo._abs_path,
                      "pmf":pmf._abs_path,
                      "testsuite": "",
                      "label": "" 
                     }
    # Sanity checks 
    if lvo.specsets.__len__() == 0: 
        raise RuntimeError("Levels file contains zero specsets!")
    column_headers = ["test-suite"]
    column_headers.append("temp-1")
    for supply in cfo.supplies: 
        column_headers.append("%s-vout"%(supply.name))
        column_headers.append("%s-ilimit-source"%(supply.name))
        column_headers.append("%s-ilimit-sink"%(supply.name))
    for pin in cfo.pins: 
        column_headers.append("%s-vih"%(pin.name))
        column_headers.append("%s-vil"%(pin.name))
        column_headers.append("%s-voh"%(pin.name))
        column_headers.append("%s-vol"%(pin.name))
        column_headers.append("%s-period"%(pin.name))
        #column_headers.append("%s-redges"%(pin.name))  
        #column_headers.append("%s-dedges"%(pin.name))
        #column_headers.append("%s-filesize"%(pin.name)) # NOTE: doesn't make sense in context of mpb, unless you summ across sequencer programs
        #column_headers.append("%s-dmas-para"%(pin.name))
        #column_headers.append("%s-dmas-sqpg"%(pin.name))
        column_headers.append("%s-vectors"%(pin.name))
        column_headers.append("%s-cycles"%(pin.name))
        column_headers.append("%s-num-of-labels"%(pin.name))
    #column_headers.append("temp-1")
    row_instances = []
    row_instance = OrderedDict()
    for ch in column_headers: 
        row_instance[ch] = 0
    temp_data = OrderedDict() 
    # ------------------------------------------------------------------------:
    if args.bbn_csv: 
        # TODO: if private-share, create alias name mapping. 
        # TODO: private the columns as well?
        ttt = 0 # total test time 
        with open(args.bbn_csv,"r") as fh: 
            for ln,line in enumerate(fh,start=1): 
                if line.startswith("#"): continue 
                if re.search("\s*,\s*,\s*",line): continue 
                line = line.strip() 
                print("DEBUG: (bbn-csv): [%s] %s"%(ln,line))
                tt,ts,tp = line.split(",")  # KEY LINE : EXTRACTS DATA. 
                #print("DEBUG: (bbn-csv): tt=%s, ts=%s, tp=%s"%(tt,ts,tp))
                _tt = float(abs(ttt - float(tt)))
                ttt = float(tt)  
                temp_data[ts.strip()] = {"temp-1":tp,"testtime":_tt}
        for ts,tsd in temp_data.items(): 
            print("DEBUG: (bbn-csv): %s: %s, (testtime = %s)"%(ts,tsd['temp-1'],tsd['testtime']))
        print("DEBUG: (bbn-csv): Total test-time: %s ms"%(ttt)) 
    # ------------------------------------------------------------------------:
    ts_no_label = set() 
    ts_bypassed = set() 
    ts_no_tim_specset = set()
    ts_no_lev_eqnset = set()

    levelgroups = OrderedDict()
    levelgroups_count = OrderedDict()
    timinggroups = OrderedDict()
    timinggroups_count = OrderedDict()
    ts_mp_ports_details = OrderedDict() # [ts] = [num,list]
    unique_mp_specsets_counts = OrderedDict()
    labels = OrderedDict()
    # ^^^ This holds a useful representation of label. 
    # NOTE: Now, we knoe that NV always uses burst from the test-suite. 
    # however, that needs to be part of our processing.
    main_labels = OrderedDict()
    mpb_labels  = OrderedDict() 

    n = 0 
    for ts in tfo.tss: # iterate through all testsuites in testflow file 
        if ts.name not in temp_data: continue 
        # ^^^ is ts is not in temp-data then there is no point in processing. 
        if ts.is_bypassed():         ts_bypassed.add(ts.name); continue 
        if not ts.get_tim_specset(): ts_no_tim_specset.add(ts.name); continue 
        if not ts.get_lvl_eqnset():  ts_no_lev_eqnset.add(ts.name); continue
        if not ts.get_label():       ts_no_label.add(ts.name); continue
        # ^^^ after ensuring we are only dealing with ts instances that are 
        # in our data set, we check for analysis requirements. We need level 
        # and timing setups, ts can be bypassed, and ts must have label. 
        n += 1
        label = ts.get_label()

        for ch in column_headers: 
            row_instance[ch] = 0.0
        row_instance['test-suite'] = ts.name
        row_instance['temp-1'] = temp_data[ts.name]["temp-1"]

        # Update setup reference: 
        setup_reference["testsuite"] = ts.name
        setup_reference["label"] = label
        # -------------------------------------------------------------------------: 
        ## Pull levels info  
        print("DEBUG: (levels): %s"%(ts.name))
        eqnset  = int(ts.get_lvl_eqnset())
        specset = int(ts.get_lvl_specset())
        levelset = int(ts.get_lvl_lvlset())
        levelgroup = "%s__%s__%s"%(eqnset,levelset,specset)
        print("[%d]: %s : Levels: EQNSET: %s, LEVELSET: %s, SPECSET: %s"%(n, ts.name,eqnset,levelset,specset))
        if levelgroup in levelgroups:
            tvs, pss = levelgroups[levelgroup]
            levelgroups_count[levelgroup] += 1
            print("---------------- REPEATED LEVELS INSTANCE--------------------")
        else: 
            tvs, pss = st7p.levels.eval_specset(lvo,eqnset*100 + specset, levelset, False)
            levelgroups[levelgroup] = [tvs,pss]
            levelgroups_count[levelgroup] = 1
        print("Config file : %s"%(cfo._abs_path))
        print("Test-suite: %s"%(row_instance['test-suite']))
        # Lets check main power lines: 
        for supply in cfo.supplies: 
            vout        = pss["dps"][supply.name]['vout']
            ilimit      = pss["dps"][supply.name]['ilimit']
            try: 
                ilimit_sink = pss["dps"][supply.name]['ilimit_sink']
            except: 
                ilimit_sink = ilimit
            try: 
                ilimit_source = pss["dps"][supply.name]['ilimit_source']
            except: 
                ilimit_source = ilimit
            #print("  %-16s, vout =%5s, ilimit = %10s, ilimit_sink = %5s"%(supply.name,vout,ilimit,ilimit_sink))
            row_instance["%s-vout"%(supply.name)] = vout
            row_instance["%s-ilimit-source"%(supply.name)] = ilimit_source
            row_instance["%s-ilimit-sink"%(supply.name)] = ilimit_sink
            #print("%20s-vout          = %s"%(supply.name,row_instance['%s-vout'%(supply.name)]))
            #print("%20s-ilimit-source = %s"%(supply.name,row_instance['%s-ilimit-source'%(supply.name)]))
            #print("%20s-ilimit-sink   = %s"%(supply.name,row_instance['%s-ilimit-sink'%(supply.name)]))
            print("%-20s: vout = %6s, ilimit-source = %6s, ilimit-sink = %6s"%(supply.name,
                row_instance['%s-vout'%(supply.name)],
                row_instance['%s-ilimit-source'%(supply.name)],
                row_instance['%s-ilimit-sink'%(supply.name)]))
        for pin in cfo.pins: 
            try: 
                row_instance["%s-vih"%(pin.name)] = pss['pins'][pin.name]['vih'] 
            except:
                row_instance["%s-vih"%(pin.name)] = 0.0 
            try: 
                row_instance["%s-vil"%(pin.name)] = pss['pins'][pin.name]['vil']
            except: 
                row_instance["%s-vil"%(pin.name)] = 0.0
            try: 
                row_instance["%s-voh"%(pin.name)] = pss['pins'][pin.name]['voh']
            except: 
                row_instance["%s-voh"%(pin.name)] = 0.0
            try: 
                row_instance["%s-vol"%(pin.name)] = pss['pins'][pin.name]['vol']
            except: 
                row_instance["%s-vol"%(pin.name)] = 0.0
            #print("%20s-vih = %s"%(pin.name,row_instance['%s-vih'%(pin.name)]))
            #print("%20s-vil = %s"%(pin.name,row_instance['%s-vil'%(pin.name)]))
            #print("%20s-vol = %s"%(pin.name,row_instance['%s-vol'%(pin.name)]))
            #print("%20s-voh = %s"%(pin.name,row_instance['%s-voh'%(pin.name)]))
            print("%-20s: vih = %6s, vil = %6s, vol = %6s, voh = %6s"%(pin.name,
                row_instance['%s-vih'%(pin.name)],
                row_instance['%s-vil'%(pin.name)],
                row_instance['%s-vol'%(pin.name)],
                row_instance['%s-voh'%(pin.name)]))
        # -------------------------------------------------------------------------: 
        ## Pull timing info  
        eqnset  = ts.get_tim_eqnset()
        specset = ts.get_tim_specset()
        timingset = ts.get_tim_timset()
        timinggroup = "%s__%s__%s"%(eqnset,timingset,specset)
        print("[%d]: %s : Timing: EQNSET: %s, TIMINGSET: %s, SPECSET: %s"%(n,ts.name,eqnset,timingset,specset))
        print("[%d]: %s : Timing:   multiport timing: %s"%(n,ts.name,ts.is_multiport_timing()))
        if ts.is_multiport_timing(): 
            if timinggroup in timinggroups: 
                print("---------------- REPEATED TIMING INSTANCE--------------------")
                ports = timinggroups[timinggroup]
                timinggroups_count[timinggroup] += 1
            else: 
                if specset not in tmo.specifications.names(): 
                    print("WARNING: %s : Specification '%s' is missing from timing object"%(ts.name,specset))
                    # ^^^ This could be due to the test-sutie being part of a bypassed block
                    
                    continue 
                ports = st7p.timing.eval_specification(tmo,specset,timingset, False)
                timinggroups[timinggroup] = ports
                timinggroups_count[timinggroup] = 1
            # -----
            ## Count unique mp-specsets
            if specset in unique_mp_specsets_counts: unique_mp_specsets_counts[specset] += 1
            else: unique_mp_specsets_counts[specset] = 1
            ## Extract multiport details: 
            timing_num_of_ports = tmo.specifications[specset].portsets.length()
            timing_port_names   = set(tmo.specifications[specset].portsets.names())
            ## per port, find out how many pins are present, We eventually want how many pins are defined. 
            timing_num_of_pins = 0
            for port in tmo.specifications[specset].portsets.names(): 
                timing_num_of_pins += cfo.ports[port].pins.__len__()
            ts_mp_ports_details[ts.name] = {"num-of-ports": timing_num_of_ports,
                                            "num-of-pins": timing_num_of_pins,
                                            "specification": specset, 
                                            "ports":timing_port_names}
            print("[%d]: %s : Timing:  Num of ports: %s"%(n,ts.name,timing_num_of_ports))
            print("[%d]: %s : Timing:  Num of pins : %s"%(n,ts.name,timing_num_of_pins))
            ## Dump contents of port definitions: 
            for port in ports: 
                #print("PORT: %s"%(port))
                #for var,val in ports[port]['vars'].items(): 
                #    print("  VAR: %-20s = %s"%(var,val))
                for pin, edges in ports[port]['pin-edges'].items(): 
                    if pin == "period": 
                        #print("  PERIOD: %s = %s"%(pin,edges)); 
                        for pin in cfo.ports[port].pins: 
                            row_instance["%s-period"%(pin)] = edges # ------------------------------------- 
                            print("%-20s: period = %s"%(pin,row_instance['%s-period'%(pin)]))
                        continue 
                    #print("  PINS: %s"%(pin))
                    #for edge,action in edges.items():
                    #    print("   %s , %s"%(edge,action))
        else: # Single Port timing  
            eqnset  = int(ts.get_tim_eqnset())
            specset = eqnset * 100 + int(ts.get_tim_specset())
            timset  = int(ts.get_tim_timset()[0])
            if timinggroup in timinggroups: 
                print("---------------- REPEATED TIMING INSTANCE--------------------")
                tvs, pes = timinggroups[timinggroup]
                timinggroups_count[timinggroup] += 1
            else: 
                tvs, pes = st7p.timing.eval_specset(tmo, specset,timset, False)
                timinggroups[timinggroup] = [tvs,pes]
                timinggroups_count[timinggroup] = 1
            for pin in cfo.pins: 
                row_instance["%s-period"%(pin.name)] = pes['period']
                print("%-20s: period = %s"%(pin.name,row_instance['%s-period'%(pin.name)]))
        #if n == timing_exit: 
        #    sys.exit(1)
        # Timing DONE
        # --------------------------------------------------------------------:
        # -------------------------------------------------------------------------: 
        ## Pull pattern info  
        #if label in labels: label_dict = labels[label]
        func = "processing-labels"
        main_label_obj = None 
        mpb_label_obj  = None
        if label in main_labels:
            main_label_obj = main_labels[label]
            print("DEBUG: (%s): NOTE: MAIN label pulled from cache: %s"%(func,label))
        elif label in mpb_labels:  
            mpb_label_obj  = mpb_labels[label]
            print("DEBUG: (%s): NOTE: MPB label pulled from cache: %s"%(func, label))
        else: 
           _labels = pmf.get(label,dd_path)
           if len(_labels) > 1:
               print("Multiple labels returned for testsuite '%s' label '%s'"%(ts.name, label))
               for j,l in enumerate(_labels):   
                   print(" %d :: %s"%(j,l))
               print(" %d :: %s"%(j+1,"exit-code"))
               err_code = j+1
               while True: 
                   ans = int(raw_input("Select label to use : "))
                   if (0 <= ans <= j): 
                       fp_label = _labels[ans]
                       break
                   elif (ans == err_code): 
                       err_msg = "More than one label return: %s"%(label)
                       err_list = _labels
                       error_log(setup_reference,err_msg,err_list)
                   else:  
                       print("input '%s' is not vaild. Try again."%(ans))
           elif len(_labels) == 0: 
               #print("WARNING: No returns for label."); continue 
               print("\nWARNING: Ts '%s' label missing: %s"%(ts.name,label))
               while True: 
                   ans = raw_input("Provide path or type 'quit'")
                   if ans == "quit": 
                       err_msg = "No labels found for label %s"%(label) 
                       error_log(setup_reference,err_msg)
                   if not os.path.isfile(ans): 
                       err_msg = "No labels found for label %s and file provide does not exist"%(label,ans) 
                   else: 
                       fp_label = ans
                       break 
           else: 
               fp_label = _labels[0]
           main_label_obj, mpb_label_obj = st7p.vectors.nvidia_vector_file_read(fp_label)
           if    main_label_obj: main_labels[label] = main_label_obj
           elif  mpb_label_obj : mpb_labels[label]  = mpb_label_obj
           else: raise RuntimeError("Unaccomidated label type: %s"%(label))
        if n >=1: 
           print("%d.) ts: %s, Label: %s, (%s,%s)"%(n,ts.name,label,main_label_obj,mpb_label_obj))
        if main_label_obj: 
            print("DEBUG: (%s): MAIN Label: %s"%(func, label))
            print("DEBUG: (%s):   - vectors: %s"%(func,main_label_obj.seq_prog.vectors))
            print("DEBUG: (%s):   - cycles : %s"%(func,main_label_obj.seq_prog.cycles))
            print("DEBUG: (%s):   - Sequencer Program:"%(func))
            for cmdno,cmdline in main_label_obj.seq_prog.program.items():
                print("DEBUG: (%s):       * [%s] %s"%(func,cmdno,cmdline))
    
            for pin in cfo.pins:
                row_instance["%s-vectors"%(pin.name)] = main_label_obj.seq_prog.vectors
                row_instance["%s-cycles"%(pin.name)]  = main_label_obj.seq_prog.cycles
                row_instance["%s-num-of-labels"%(pin.name)] = 1
                print("%-20s: vectors = %-12s, cycles = %-12s, num-of-lbls = 1"%(pin,main_label_obj.seq_prog.vectors,main_label_obj.seq_prog.cycles))
           
        elif mpb_label_obj: 
            print("DEBUG: (%s): MPB Label: %s"%(func, label))
            total_pins_in_mpb = {}
            for port in mpb_label_obj.ports: 
                #print("DEBUG: (%s):   * port: %s"%(func,port.name))
                for ii,pin in enumerate(cfo.ports[port.name].pins,start=1):  
                    #print("DEBUG: (%s):     %3d.) pin: %s"%(func,ii,pin))
                    if pin in total_pins_in_mpb: 
                        raise RuntimeError("Double instance of pin in mpb-ports: %s"%(pin))
                    else: total_pins_in_mpb[pin] = port
            print("DEBUG: (%s): MPB Label ports: %s"%(func, mpb_label_obj.ports.__len__())) 
            print("DEBUG: (%s): MPB Label pins : %s"%(func, len(total_pins_in_mpb))) 
           
            port_to_vectors_and_cycles = {} #{"vectors":0,"cycles":0}
            #for port, seq_prog in mpb_label_obj.ports.items(): # MPBLabel.ports[port] = seq-prog
            for port in mpb_label_obj.ports: # MPBLabel.ports[port] = seq-prog
                print("DEBUG: (%s): Port %s, label = %s"%(func,port.name,label)) 
                port_to_vectors_and_cycles[port.name] = {"vectors":0,"cycles":0,'num-of-labels':0}

                print(port.seq_prog.program.items())
                for cmdno, sqpg in port.seq_prog.program.items(): 
                    if sqpg['instr'] == "CALL": 
                        call_main_label = sqpg['param2'].strip("\"")
                        if call_main_label in main_labels: pass
                        else: 
                            __labels = pmf.get(call_main_label,dd_path)
                            if len(__labels) > 1:  raise RuntimeError("ERROR: More than one label return: %s"%(call_main_label))
                            if len(__labels) == 0: print("WARNING: No returns for label."); continue 
                            print("DEBUG: (%s): %s: parsing: %s"%(func,port,__labels[0]))
                            main_labels[call_main_label] , _ = st7p.vectors.nvidia_vector_file_read(__labels[0])
                        # Extract the vectors and cycles per main-label
                        port_to_vectors_and_cycles[port.name]["vectors"] += main_labels[call_main_label].seq_prog.vectors
                        port_to_vectors_and_cycles[port.name]["cycles"]  += main_labels[call_main_label].seq_prog.cycles
                        port_to_vectors_and_cycles[port.name]["num-of-labels"]  += 1
            #if n >=1: sys.exit(1) 
            print("DEBUG: (%s): MPB Label: %s"%(func, label))
            print(mpb_label_obj.sfp)
            for port, vac in port_to_vectors_and_cycles.items():
                print("DEBUG: (%s): %-20s: vectors = %-12s, cycles = %-12s, num-of-lbls = %s"%(func,port,vac['vectors'],vac['cycles'],vac['num-of-labels']))
                for pin in cfo.ports[port].pins: 
                    row_instance["%s-vectors"%(pin)] = vac['vectors']
                    row_instance["%s-cycles"%(pin)] = vac['cycles']
                    row_instance["%s-num-of-labels"%(pin)] = vac['num-of-labels']
                    print("%-20s: vectors = %-12s, cycles = %-12s, num-of-lbls = %s"%(pin,vac['vectors'],vac['cycles'],vac['num-of-labels']))
            #for port, seq_prog in mpb_label_obj.ports.items(): 
            for port in mpb_label_obj.ports: 
                port_pins = cfo.ports[port.name].pins
                print("DEBUG: (%s): Port pins: %s"%(func,port))
                for ii,pin in enumerate(port_pins,start=1): 
                    print("DEBUG: (%s):   %3d.) %s"%(func,ii,pin))
                k = 0
                for cmdno, sqpg in port.seq_prog.program.items(): 
                    if k == 0 : 
                        if sqpg['instr'] == "CALL": 
                            print("DEBUG: (%s): %20s | %s"%(func, port, sqpg['param2']))
                        elif sqpg['instr'] == "BEND": 
                            print("DEBUG: (%s): %20s | %s"%(func, port, sqpg['instr']))
                        else: raise RuntimeError("Unexpected instruction: %s; %s"%(sqpg['instr'],label))
                    else: 
                        if sqpg['instr'] == "CALL": 
                            print("DEBUG: (%s): %20s | %s"%(func, "", sqpg['param2']))
                        elif sqpg['instr'] == "BEND": 
                            print("DEBUG: (%s): %20s | %s"%(func, "", sqpg['instr']))
                        else: raise RuntimeError("Unexpected instruction: %s; %s"%(sqpg['instr'],label))
                    k += 1
        else: 
            raise RuntimeError("Unidentifier Label type: %s"%(_labels[0]))
        # Store row instance: 
        row_instances.append(read_out_values(row_instance))
    # Results: 
    #for row in row_instances: 
    #    print(row) 
    # Some results: 
    with open("test_data.csv","w") as writer: 
        header = ",".join(column_headers) + "\n"
        writer.write(header)
        for x in row_instances: 
            y = ",".join(x) + "\n"
            writer.write(y)
    print("Number of columns: %s"%(column_headers.__len__()))
    print("Number of inputs : %s"%(len(column_headers) - 4))

  
       
        
         


     


    

    
