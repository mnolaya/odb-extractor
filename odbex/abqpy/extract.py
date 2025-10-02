import copy


from ._json import load_json_py2
from .extractor import (
    ExtractionDefinition, 
    OdbExtractor, 
    DEFAULT_CONFIG_SETTINGS, 
    OutputWriter
)

def build_extraction_regions(extractor_config):
    # type: (dict) -> list[ExtractionDefinition]
    extraction_definitions = []
    for e in extractor_config["extract"]:
        # Copy over the default settings and update with the user settings
        settings = copy.deepcopy(DEFAULT_CONFIG_SETTINGS["extract"])
        settings.update(**e)

        extraction_definitions.append(ExtractionDefinition(
            e["component"],
            e["mesh_type"],
            e["label"],
            e["fields"],
            e["average"],
        ))
    return extraction_definitions

def main(odb_fp, odbex_cfg_fp):
    # Prepare OdbExtractor for extraction
    odbex_cfg = load_json_py2(odbex_cfg_fp)
    extraction_definitions = build_extraction_regions(odbex_cfg)
    odbex = OdbExtractor(odb_fp, extraction_definitions)

    # Extract data from the odb
    try:
        step_names = odbex_cfg["steps"]
    except KeyError:
        step_names = odbex.odb.steps.keys()
    extracted_data = []
    for step_name in step_names:
        odbex.load_analysis_frames(step_name)
        extracted_data += odbex.extract_odb_data()

    # Create writer and write to npz filetype
    writer = OutputWriter(odbex, extracted_data, output_dir=r"G:\My Drive\repos\odb-extractor\tests")
    writer.write_npz()
    
    # Close odb
    odbex.close_odb()

if __name__ == "__main__":
    test_odb = r"C:\Users\Michael_Olaya\abqlocal\rsoc\microscale_interface_model\06\analysis_000\analysis_000.odb"
    # test_odb = r"C:\Users\micha\abqlocal\rsoc\unit_tests_mm\jobs_model_1_linear_full\unit_test_axisym_cohesive_surf_0\unit_test_axisym_cohesive_surf_0.odb"
    test_cfg = r"G:\My Drive\repos\odb-extractor\tests\test_cfg.json"

    main(test_odb, test_cfg)