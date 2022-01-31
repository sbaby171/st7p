""" 
This script processes a testflow file and its primary setups. Mainly, 
the pin configuraiton, timing, levels, and vectors file. 
"""
import st7p.testflow
import st7p.config
import st7p.timing
import st7p.levels
import st7p.vectors
import sys, os, re, argparse
from collections import OrderedDict
# ----------------------------------------------------------------------------:
def __handle_cmd_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", 
                        help="debug printing",
                        action="store_true")
    parser.add_argument("-make_smt8_config",
                        help="create smt8 configuration setups",
                        action="store_true")
    parser.add_argument("-tf",help="testflow file")
    parser.add_argument("-ts",help="test-suite name")
    parser.add_argument("-test",
                        help="execute testing checks",
                        action="store_true")
    args = parser.parse_args()
    # Testflow file:  
    if not args.tf: 
        raise RuntimeError("Must provide testflow file '-tf'")
    if not os.path.isfile(args.tf): 
        raise RuntimeError("Testflow doesn't exist or has bad permissions.")
    # EDF file:  
    if args.edf: 
        if not os.path.isfile(args.edf): 
            raise RuntimeError("EDF doesn't exist or has bad permissions.")
    return args
# ----------------------------------------------------------------------------:
if __name__ == "__main__": 
    func = sys.argv[0][:-3] + ".main"
    args = __handle_cmd_args()
    debug = args.debug
    # ------------------------------------------------------------------------:
    # Testflow and setup files
    # ------------------------------------------------------------------------:
    tfo = st7p.testflow.read(args.tf,debug)               # 1
    cfo = st7p.config.read(tfo.get_config_path(),debug)   # 2
    tmo = st7p.timing.read(tfo.get_timing_path(),debug)   # 3 
    lvo = st7p.levels.read(tfo.get_levels_path(),debug)   # 4
    vco = st7p.vectors.read(tfo.get_vectors_path(),debug) # 5
    # ------------------------------------------------------------------------:
    # Setup Summaries: 
    # ------------------------------------------------------------------------:
    _masked = True  # Mask source file paths. 
    tfo.summary(mask=_masked)
    cfo.summary(mask=_masked) 
    lvo.summary(mask=_masked)
    tmo.summary(mask=_masked)
    vco.summary(mask=_masked)
