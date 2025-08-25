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

To extract field data from an Abaqus ODB using this package, you will need to create a config file which defines what data is specifically to be extracted and where it should be extracted from (e.g., region, field names). Refer to the [example](example_cfg.json). A few notes:

1. Field names are as per the Abaqus documentation, e.g. `S` for stress, `E` for engineering strain. 
2. State variables must be requested on a per-index basis, i.e. `SDV1` must be explicitly requested as opposed to generally `SDV`.
3. The `nframes` key in the [example](example_cfg.json) is set to `null` -- this means that all frames from the output will be extracted. If you want less than the total number of frames, set this to some integer value and the extractor will grab data at evenly spaced intervals accordingly.
4. The file can be named anything you want.

## Extracting

### Single ODB

Once you have your extraction config file, running an extraction for a single ODB is simple.

```bash
python -m odbex path_to_odb.odb path_to_config.json
```

### Batch ODB

You can also run a batch extraction of multiple ODBs using wildcard syntax (`*`). For example, to get all odbs from folder `some_folder`:

```bash
python -m odbex some_folder\*.odb path_to_config.json
```

Or, to get data from all ODBs that contain `55pct` in the file name from folder `some_folder`:

```bash
python -m odbex some_folder\*55pct*.odb path_to_config.json
```

In either case (single or batch mode), the extracted data will be output in `.json` file format with the same base name as the extracted ODB(s) and a prefix defined by the `export_prefix` key in the config file. 

> [!NOTE]
> Output data is averaged (or volume-averaged, in the case of stress and strain) across the requested region. Standard deviations are provided in the extracted output file.

> [!NOTE]
> Maximum principal stress/strain are automatically extracted when requesting `S` and `E` fields.

## Data exploration

A submodule called `odbex.post` contains functionality to read in this data for further plotting/data exploration. Refer to the brief [example notebook](./tests/test_results.ipynb) for how to use `odbex.post`.