import copy


from ._json import load_json_py2
from .extract import (
    ExtractionDefinition, 
    OdbExtractor, 
    DEFAULT_CONFIG_SETTINGS, 
    OutputWriter
)

if __name__ == "__main__":
    test_odb = r"C:\Users\Michael_Olaya\abqlocal\rsoc\microscale_interface_model\06\analysis_000\analysis_000.odb"
    # test_odb = r"C:\Users\micha\abqlocal\rsoc\unit_tests_mm\jobs_model_1_linear_full\unit_test_axisym_cohesive_surf_0\unit_test_axisym_cohesive_surf_0.odb"
    test_cfg = r"G:\My Drive\repos\odb-extractor\tests\test_cfg.json"

    main(test_odb, test_cfg)