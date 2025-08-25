# Requirements

1. Python 3.10+
2. Abaqus 2019+

# Installation

This package is a Python 3 wrapper around the Abaqus Python installation. Thus, it must be installed in your Python 3 environment. In editable mode:

```bash
cd path\to\odb-extractor
pip install -e .
```

Note that you may get a warning upon installing regarding legacy editable installs. Ignore it.

# Quick start guide

## Configuration file

To extract field data from an Abaqus ODB using this package, you will need to create a config file which defines what data is specifically to be extracted and where it should be extracted from (e.g., region, field names). Refer to the [example](.\example_cfg.json). A few notes:

1. Field names are as per the Abaqus documentation, e.g. `S` for stress, `E` for engineering strain. 
2. State variables must be requested on a per-index basis, i.e. `SDV1` must be explicitly requested as opposed to generally `SDV`.
3. The `nframes` key in the [example](.\example_cfg.json) is set to `null` -- this means that all frames from the output will be extracted. If you want less than the total number of frames, set this to some integer value and the extractor will grab data at evenly spaced intervals accordingly.
4. The file can be named anything you want.

## Extracting

Once you have your extraction config file, running an extraction for a single ODB is simple.

```bash
python -m odbex path_to_odb.odb path_to_config.json
```

The extracted data will be output in `.json` file format with the same base name as the ODB with a prefix defined by the `export_prefix` key. 

## Data exploration

A submodule called `odbex.post` contains functionality to read in this data for further plotting/data exploration. Refer to the brief example notebook for how to use `odbex.post`.