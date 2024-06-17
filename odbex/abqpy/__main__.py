import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse

from abqpy import extractor, _json

def _argparse():
    # type: () -> argparse.Namespace
    parser = argparse.ArgumentParser()
    parser.add_argument('odb', default=None)
    parser.add_argument('cfg', default=None)
    return parser.parse_args()
    
def main():
    # type: () -> None
    args = _argparse()

    # Load configuration settings for the extraction
    odbex_cfg = _json.load_json_py2(args.cfg)

    # Call extractor
    extractor.extract(args.odb, odbex_cfg)
    
if __name__ == "__main__":
    main()