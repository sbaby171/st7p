import sys, os, argparse 
import config,testflow,vectors,timing,levels

def help_menu(args): 
    retstr    =  ["\nst7p interactive mode: ",
                     "=====================:"]
    if args.config: 
        retstr.append("\nConfig file -> object reference `cfo`:")
        retstr.append(  "-------------------------------------:")
        retstr.append(  "cfo.summary() # Dump high-level summary report of config file.")
        retstr.append("") 
        retstr.append("\nVector file -> object reference `vfo`:")
        retstr.append(  "-------------------------------------:")
        retstr.append(  "vfo.summary() # Dump high-level summary report of vector file.")
        retstr.append("") 

    return "\n".join(retstr)

def __handle_cmdline_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", help="increase output verbosity.",
                         action="store_true")
    parser.add_argument("-config",   help="pin-config file path",)
    parser.add_argument("-testflow", help="testflow file path",)
    parser.add_argument("-vector",   help="vector file path",)
    parser.add_argument("-timing",   help="timing file path",)
    parser.add_argument("-levels",   help="levels file path",)
    args = parser.parse_args()

    if not (args.config or args.testflow or args.vector or args.timing or args.levels): 
        error_msg = "ERROR: Must provide a file.\n"\
                    "  -config   <config-file>\n"\
                    "  -testflow <testflow-file>\n"\
                    "  -timing   <timing-file>\n"\
                    "  -levels   <levels-file>\n"\
                    "  -vectors  <vectors-file>\n"
        raise ValueError(error_msg)
    return args
#-----------------------------------------------------------------------------:
if __name__ == "__main__":
    args = __handle_cmdline_args()

    if args.config: 
        cfo = config.read(sfp=args.config,debug=args.debug)
        print("\nSUCCESS: Configuration file parsed: use object reference 'cfo' for internal information.")
    if args.testflow: 
        tfo = testflow.read(sfp=args.testflow,debug=args.debug)
    if args.vector: 
        vfo = vectors.read(sfp=args.vector,debug=args.debug)
    if args.timing: 
        tmo = timing.read(sfp=args.timing,debug=args.debug)
    if args.levels: 
        lvo = levels.read(sfp=args.levels,debug=args.debug)

    print(help_menu(args))
