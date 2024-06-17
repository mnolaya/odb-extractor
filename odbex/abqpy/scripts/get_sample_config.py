import os, shutil

ROOT = os.path.dirname(os.path.dirname(__file__))

def main():
    sample_config_path = os.path.join(ROOT, "_config", "config.json")
    shutil.copy(sample_config_path, os.getcwd())
    print("\nA sample odb extraction config has been copied to your current working directory:\n{}\n".format(os.path.join(os.getcwd(), "config.json")))

if __name__ == "__main__":
    main()