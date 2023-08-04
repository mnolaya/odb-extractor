import argparse
import odbex as oex

def _argparse():
    # type: () -> argparse.ArgumentParser
    parser = argparse.ArgumentParser(prog="odbex")
    parser.add_argument("config", nargs="?", default=None, help="Path to .json file containing extraction configuration.")
    return parser.parse_args()
    
def main():
    # type: () -> None
    args = _argparse()
    if args.config is None:
        print("\nError! You must provide an odb extraction configuration file in .json file format. To get a sample config.json, run: abaqus python -m odbex.scripts.get_sample_config.\n")
        return
    oex.scripts.extract_odb_field_data.main(args)
    
if __name__ == "__main__":
    main()