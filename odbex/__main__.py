import argparse
import pathlib
import subprocess

PARENT = pathlib.Path(__file__).parent
EXTRACTOR = PARENT.joinpath('abqpy/__main__.py')

def _argparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="odbex")
    parser.add_argument('odb', help='Full or relative path to output database (.odb) file.')
    parser.add_argument('cfg', help='Full or relative path to odbex configuration (odbex_cfg.json) file.')
    parser.add_argument('--mode', help='Output data write mode. Options are: numpy', default='numpy')
    parser.add_argument('--output_dir', help='Directory to write output to. Defaults to the same directory as the odb that was extracted from.', default=None)
    return parser.parse_args()

def main() -> None:
    args = _argparse()
    if args.output_dir is not None:
        output_dir = pathlib.Path(args.output_dir).absolute()
    else:
        output_dir = "None"
    subprocess.run([
        'abaqus',
        'python',
        'abqpy/__main__.py',
        pathlib.Path(args.odb).absolute(),
        pathlib.Path(args.cfg).absolute(),
        args.mode,
        output_dir
    ],
    check=True,
    shell=True,
    cwd=PARENT
    )

if __name__ == "__main__":
    main()