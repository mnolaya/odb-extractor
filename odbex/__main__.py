import argparse
import pathlib
import subprocess
import os
import signal
import json

PARENT = pathlib.Path(__file__).parent
EXTRACTOR = PARENT.joinpath('abqpy/_extract.py')

def _argparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="odbex")
    parser.add_argument('odb', help='Full or relative path to output database (.odb) file.')
    parser.add_argument('cfg', help='Full or relative path to odbex configuration (odbex_cfg.json) file.')
    return parser.parse_args()

def main() -> None:
    args = _argparse()

    # Get config and set up extraction data directory
    with open(args.cfg, 'r') as f:
        odbex_cfg = json.load(f)
    data_dir = pathlib.Path(odbex_cfg['export']).joinpath('raw_odbex')
    if not data_dir.exists(): data_dir.mkdir()


    p = subprocess.Popen(['abaqus', 'python', EXTRACTOR.as_posix(), args.odb, args.cfg], preexec_fn=os.setsid)
    while True:
        if p.poll() is not None:
            break
        try:
            p.wait()
        except KeyboardInterrupt:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)     

if __name__ == '__main__':
    main()