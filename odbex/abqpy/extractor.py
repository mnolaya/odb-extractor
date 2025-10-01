from odbAccess import openOdb

from abqpy import extract

class ExtractionDefinition:

    def __init__(self, model_component_name, mesh_type, group_by, groups, fields):
        # type: (str, str, str, str | list[str | int], list[str]) -> None
        self.model_component_name = model_component_name
        self.mesh_type = mesh_type
        self.group_by = group_by
        self.groups = groups
        self.fields = fields

class OdbExtractor:

    def __init__(self, odb_filepath, extraction_definitions):
        # type: (str, list[ExtractionDefinition]) -> None
        self.odb = openOdb(odb_filepath)
        self.extraction_definitions = extraction_definitions

    # def 

    

    