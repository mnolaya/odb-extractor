import numpy as np

import abaqusConstants as abqconst
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

def terminate_region_keyerror(model_component_name, region_label):
    print('error: {} does not exist on {}'.format(region_label, model_component_name))
    print('terminating...')
    exit()

def _slice_frames_evenly(frames, num_frames=None):
    # type: (int, int | None) -> list[OdbFrame]
    
    # Check if number of frames is provided or if it exceeds the number of available frames 
    total_frames = len(frames)
    if num_frames >= total_frames or num_frames is None: return frames
    
    # Create evenly spaced slice indices
    # Ensure that the last frame is always included
    indices = list(np.arange(0, total_frames, round(total_frames/num_frames), dtype=int))
    if indices[-1] != total_frames-1: indices.append(total_frames-1)
    return [frames[i] for i in indices]

class ExtractionDefinition:

    def __init__(self, model_component_name, mesh_type, label, fields):
        # type: (str, str, str, str | int, list[str]) -> None
        self.model_component_name = model_component_name
        self.mesh_type = mesh_type
        self.label = label
        self.fields = fields
        # self.region = None

    def validate_region(self, model_component):
        valid = True
        if self.mesh_type == 'element' and type(self.label) == str:
            if self.label not in model_component.elementSets.keys(): valid = False
        elif self.mesh_type == 'element' and type(self.label) == int:
            try:
                model_component.getElementFromLabel(self.label)
            except:
                valid = False
        elif self.mesh_type == 'node' and type(self.label) == str:
            if self.label not in model_component.nodeSets.keys(): valid = False
        elif self.mesh_type == 'node' and type(self.label) == int:
            try:
                model_component.getNodeFromLabel(self.label)
            except:
                valid = False
        return valid

class OdbExtractor:

    def __init__(self, odb_filepath, extraction_definitions):
        # type: (str, list[ExtractionDefinition]) -> None
        self.odb = openOdb(odb_filepath)
        self.extraction_definitions = extraction_definitions
        self.step_name = ''
        self.frames = []
        self.region = None

    def load_analysis_frames(self, step_name, num_frames=None):
        # type: (str, int | None) -> None
        self.step_name = step_name
        self.frames = _slice_frames_evenly(self.odb.steps[step_name].frames, num_frames)

    def set_extraction_region(self, extraction_definition):
        # type: (ExtractionDefinition) -> None

        # Get the requested assembly or instance
        ed = extraction_definition
        if ed.model_component_name.lower() == 'assembly':
            model_component = self.odb.rootAssembly
        else:
            try:
                model_component = self.odb.rootAssembly.instances[ed.model_component_name]
            except KeyError:
                terminate_instance_keyerror(ed.model_component_name, self.odb.rootAssembly.instances)
        
        # Terminate if the requested region is not valid
        if not ed.validate_region(model_component):
            label_ = ed.label
            if type(ed.label) == int: label_ = ed.mesh_type[0].upper() + str(ed.label)
            terminate_region_keyerror(ed.model_component_name, label_)

        # Get the region from the odb
        if ed.mesh_type == 'element' and type(ed.label) == str:
            self.region = model_component.elementSets[ed.label]
        elif ed.mesh_type == 'element' and type(ed.label) == int:
            self.region = model_component.getElementFromLabel(ed.label)
        elif ed.mesh_type == 'node' and type(ed.label) == str:
            self.region = model_component.nodeSets[ed.label]
        elif ed.mesh_type == 'node' and type(ed.label) == int:
            self.region = model_component.getNodeFromLabel(ed.label)

    def get_field_data(self, field_name):
        # Get the field data for each frame on the current extraction region
        fd = []
        get_components = True
        for frame in self.frames:
            # Get all field output for current field and frame
            field_data = frame.fieldOutputs[field_name]

            # Get component labels for the field
            if get_components: 
                components = list(field_data.componentLabels)
                if not components: components = [field_name]
                get_components = False

            # Use the bulkDataBlocks method to retrieve all field output data for the region
            bdbs = field_data.getSubset(region=self.region).bulkDataBlocks
            
            # Stack data into numpy array
            data_arr = np.vstack(bdb.data for bdb in bdbs)

            # Get max. principal if stress or strain requested
            if field_name in ['S', 'E', 'LE']:
                bdbs = field_data.getSubset(region=self.region).getScalarField(invariant=abqconst.MAX_PRINCIPAL).bulkDataBlocks
                data_arr = np.hstack([data_arr, np.vstack(bdb.data for bdb in bdbs)])
                components += ("{}MAXPRINC".format(field_name), )
        # return data, components
        # Get the specific requested region on the model component
        

    # def _get_instance_element_set_region(self, odb):
    #     try:
    #         instance = odb.rootAssembly.instances[self.model_component_name]
    #     except KeyError:
    #         terminate_instance_keyerror(self.model_component_name, odb.rootAssembly.instances)
    #     return [instance.elementSets[group] for group in self.groups]


    # def extract(self):
        # ed = self.extraction_definitions[0]
        # ed.get_extraction_region(self.odb)
        
        # print(ed.)

        # for ed in self.extraction_definitions:
            # print(ed.label)

    # def    

    