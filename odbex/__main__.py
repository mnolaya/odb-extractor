import argparse
import pathlib
import subprocess

PARENT = pathlib.Path(__file__).parent
EXTRACTOR = PARENT.joinpath('abqpy/__main__.py')

def _argparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="odbex")
    parser.add_argument('odb', help='Full or relative path to output database (.odb) file.')
    parser.add_argument('cfg', help='Full or relative path to odbex configuration (odbex_cfg.json) file.')
    parser.add_argument('mode', nargs="?", help='Output data write mode. Options are: numpy', default='numpy')
    parser.add_argument('output_dir', nargs="?", help='Directory to write output to. Defaults to the same directory as the odb that was extracted from.', default=None)
    return parser.parse_args()

def main() -> None:
    args = _argparse()
    subprocess.run(['abaqus', 'python', 'abqpy/__main__.py', args.odb, args.cfg, args.mode, str(args.output_dir)], check=True, shell=True, cwd=PARENT)

if __name__ == "__main__":
    main()