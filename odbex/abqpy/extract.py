# import os
# import json
# import sys

# import numpy as np

# from odbAccess import openOdb
# import abaqusConstants as abqconst

from abqpy.extractor import ExtractionDefinition

def build_extraction_regions(extractor_config):
    # type: (dict) -> list[ExtractionDefinition]
    extraction_definitions = []
    for e in extractor_config["extract"]:
        extraction_definitions.append(ExtractionDefinition(
            e["component"],
            e["mesh_type"],
            e["group_by"],
            e["groups"],
            e["fields"],
        ))
    return extraction_definitions

if __name__ == "__main__":
    from abqpy._json import load_json_py2

    test_cfg = load_json_py2(r"G:\My Drive\repos\odb-extractor\tests\test_cfg.json")
    extraction_definitions = build_extraction_regions(test_cfg)
    print(extraction_definitions[0].mesh_type)