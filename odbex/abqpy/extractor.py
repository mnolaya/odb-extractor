from odbAccess import openOdb

# from abqpy import extract

def terminate_instance_keyerror(instance_name, instances):
    # type: (str, dict) -> None
    print('error: instance {} does not exist'.format(instance_name))
    print('the instances on the model which field data can be extracted from are:')
    for inst in instances.keys():
        print('-> {}'.format(inst))
    print('terminating...')
    exit()

class ExtractionDefinition:

    # region_getters = {
    #     'assembly': {
    #         'element': {
    #             'set': _get_instance_element_set_region,
    #             'number': get_instance_elements_by_number,
    #         },
    #         'node': {
    #             'set': get_instance_node_set,
    #             'number': get_instance_nodes_by_number,
    #         },
    #     },        
    # }

    def __init__(self, model_component_name, mesh_type, group_by, groups, fields):
        # type: (str, str, str, str | list[str | int], list[str]) -> None
        self.model_component_name = model_component_name
        self.mesh_type = mesh_type
        self.group_by = group_by
        self.groups = groups
        self.fields = fields
        self.region = None

    def get_extraction_region(self, odb):
        # type: (Odb) -> list

        # Get the assembly or instance
        if self.model_component_name.lower() == 'assembly':
            model_component = odb.rootAssembly
        else:
            try:
                model_component = odb.rootAssembly.instances[self.model_component_name]
            except KeyError:
                terminate_instance_keyerror(self.model_component_name, odb.rootAssembly.instances)
        getters = {
            ''
        }

    def _get_instance_element_set_region(self, odb):
        try:
            instance = odb.rootAssembly.instances[self.model_component_name]
        except KeyError:
            terminate_instance_keyerror(self.model_component_name, odb.rootAssembly.instances)
        return [instance.elementSets[group] for group in self.groups]

    # def _get_instance_node_set_region(self, odb):
    #     pass

    # def _get_assembly_element_set_region(self, odb):
    #     pass

    # def _get_assembly_node_set_region(self, odb):
    #     pass

class OdbExtractor:

    def __init__(self, odb_filepath, extraction_definitions):
        # type: (str, list[ExtractionDefinition]) -> None
        self.odb = openOdb(odb_filepath)
        self.extraction_definitions = extraction_definitions

    # def 

    

    