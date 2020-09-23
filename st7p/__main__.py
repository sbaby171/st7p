import pins 
import sys, os, argparse
def __handle_cmdline_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="increase output verbosity.",
                         action="store_true")
    parser.add_argument("--pinconfig",help="pin-config file path",)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    print("\nst7p direct\n")
    args = __handle_cmdline_args()

    if args.pinconfig: 
        pco = pins.read_pinconfig(sfp=args.pinconfig,debug=args.debug)


