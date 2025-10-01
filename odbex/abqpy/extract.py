# import os
# import json
# import sys

# import numpy as np

# from odbAccess import openOdb
# import abaqusConstants as abqconst

from extractor import ExtractionDefinition, OdbExtractor

def build_extraction_regions(extractor_config):
    # type: (dict) -> list[ExtractionDefinition]
    extraction_definitions = []
    for e in extractor_config["extract"]:
        extraction_definitions.append(ExtractionDefinition(
            e["component"],
            e["mesh_type"],
            e["label"],
            e["fields"],
        ))
    return extraction_definitions

if __name__ == "__main__":
    from abqpy._json import load_json_py2

    test_odb = r"C:\Users\micha\abqlocal\rsoc\unit_tests_mm\jobs_model_1_linear_full\unit_test_axisym_cohesive_surf_0\unit_test_axisym_cohesive_surf_0.odb"
    test_cfg = load_json_py2(r"G:\My Drive\repos\odb-extractor\tests\test_cfg.json")

    # Prepare OdbExtractor for extraction
    extraction_definitions = build_extraction_regions(test_cfg)
    extractor = OdbExtractor(test_odb, extraction_definitions)

    # Load desired step frames to extract from
    extractor.load_analysis_frames("Step-1")
    
    extractor.get_extraction_region(extractor.extraction_definitions[0])
    # 
    