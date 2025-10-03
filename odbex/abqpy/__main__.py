import os
import sys
import glob
import argparse

from abqpy import extract

def _argparse():
    # type: () -> argparse.Namespace
    parser = argparse.ArgumentParser()
    parser.add_argument('odb', default=None)
    parser.add_argument('cfg', default=None)
    parser.add_argument('mode', default='numpy')
    parser.add_argument('output_dir', default=None)
    return parser.parse_args()
    
def main():
    # type: () -> None
    args = _argparse()

    # Resolve str to None type
    if args.output_dir.lower() == 'none':
        args.output_dir = None
    
    # Gather multiple odbs if wildcard option used
    if '*' in args.odb:
        odbs = list(glob.glob(args.odb))
    else:
        odbs = [args.odb]

    # Extract from all odbs requested
    for odb in odbs:
        # Set the output directory
        output_dir = args.output_dir
        if output_dir is None: output_dir = os.path.dirname(odb)

        # Run extractor
        print('extracting from -> {}...'.format(odb))
        extract.extract_from_odb(odb, args.cfg, args.mode, output_dir)
    
if __name__ == "__main__":
    main()