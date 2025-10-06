import os
import copy

import numpy as np
from math import pi

import abaqusConstants as abqconst
from odbAccess import openOdb

from ._json import load_json_py2

DEFAULT_CONFIG_SETTINGS = {
    "extract": {
        "average": "arthimetic"
    },
    "nframes": None,
    "export_prefix": "odbex"
}

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
    # type: (list[OdbFrame], int | None) -> list[OdbFrame]
    
    # Check if number of frames is provided or if it exceeds the number of available frames 
    total_frames = len(frames)
    if num_frames is None or num_frames >= total_frames: return frames
    
    # Create evenly spaced slice indices
    # Ensure that the last frame is always included
    indices = list(np.arange(0, total_frames, round(total_frames/num_frames), dtype=int))
    if indices[-1] != total_frames-1: indices.append(total_frames-1)
    return [frames[i] for i in indices]

class FieldData:

    def __init__(self, data, components, step_name, field_name, extraction_definition):
        self.data = data
        self.components = components
        self.id = '|'.join([
            step_name,
            extraction_definition.model_component_name, 
            extraction_definition.label,
            extraction_definition.mesh_type,
            field_name
        ])
        self.avg = None
        self.std = None

    def arthimetic_average(self):
        # type: () -> None
        # Compute average and standard deviation for each frame of data
        avg, std = [], []
        for i in range(self.data.shape[0]):
            avg.append(np.mean(self.data[i], axis=0))
            std.append(np.std(self.data[i], axis=0))
        self.avg = np.array(avg)
        self.std = np.array(std)

    def volume_average(self, ivols):
        # type: (np.ndarray) -> None
        # Compute average and standard deviation for each frame of data
        avg, std = [], []
        for i in range(self.data.shape[0]):
            avg.append(np.sum(self.data[i]*ivols, axis=0)/np.sum(ivols))
            std.append(np.std(self.data[i]*ivols, axis=0))
        self.avg = np.array(avg)
        self.std = np.array(std)

    def axisymmetric_area_weight(self, node_coordinates, axis=0):
        # type: (list[np.ndarray], int) -> None
        pos = [c[axis] for c in node_coordinates]
        weights = []

        # Compute weights for node pairs along surface
        for x0, x1 in zip(pos[:-1], pos[1:]):
            dx = abs(x1 - x0)
            mid = 0.5*(x1 + x0)
            weights.append([2*pi*mid*dx])
        weights_arr = np.array(weights)

        # Compute average and standard deviation for each frame of data
        avg, std = [], []
        for i in range(self.data.shape[0]):
            fd_ = []
            for fd0, fd1 in zip(self.data[i, :-1], self.data[i, 1:]):
                fd_.append(0.5*(fd0 + fd1))
            fd_arr = np.array(fd_)
            avg.append(np.array([np.sum(fd_arr*weights_arr)/np.sum(weights_arr)]))
            std.append([np.std([fd_arr*weights_arr])])
        self.avg = np.array(avg)
        self.std = np.array(std)

class ExtractionDefinition:

    def __init__(self, model_component_name, mesh_type, label, fields, average='arthimetic'):
        # type: (str, str, str | int, list[str], str) -> None
        self.model_component_name = model_component_name
        self.mesh_type = mesh_type
        self.label = label
        self.fields = fields
        self.average_mode = average
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
        self._curr_extraction_definition = None

    def close_odb(self):
        self.odb.close()

    def load_analysis_frames(self, step_name, num_frames=None):
        # type: (str, int | None) -> None
        self.step_name = step_name
        self.frames = _slice_frames_evenly(self.odb.steps[step_name].frames, num_frames)

    def set_extraction_region(self, extraction_definition):
        # type: (ExtractionDefinition) -> None
                
        # Update the current extraction definition
        self._curr_extraction_definition = extraction_definition

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

    @staticmethod
    def get_field_data_components(field_data):
        components = list(field_data.componentLabels)
        if not components: components = [field_data.name]
        return components

    @staticmethod
    def get_invariants(field_data):
        return field_data.validInvariants
    
    def get_valid_fields(self, region_name, frame_index):
        # type: (str, int) -> list[str]
        valid_fields = []
        for field_name in self.frames[frame_index].fieldOutputs.keys():
            if region_name in field_name: valid_fields.append(field_name)
        return valid_fields

    def get_region_field_data(self, field_name):
        # type: (str) -> FieldData
        
        # Get component labels for the field
        components = self.get_field_data_components(self.frames[0].fieldOutputs[field_name])

        # Get the field data for each frame on the current extraction region
        fd = []
        for frame in self.frames:
            # Get all field output for current field and frame
            field_data = frame.fieldOutputs[field_name]

            # Use the bulkDataBlocks method to retrieve all field output data for the region
            bdbs = field_data.getSubset(region=self.region).bulkDataBlocks
            
            # Stack data into numpy array
            fd.append(np.vstack(bdb.data for bdb in bdbs))
        return FieldData(np.array(fd), components, self.step_name, field_name, self._curr_extraction_definition)
    
    def extract_odb_data(self):
        extracted_data = []
        for ed in self.extraction_definitions:
            # Set the current region for field data extraction
            self.set_extraction_region(ed)
            
            # Get integration point volumes for the region if volume-averaging mode set
            if ed.average_mode == 'volume':
                fd_ivol = self.get_region_field_data("IVOL")

            # Get all requested fields on the region
            for field in ed.fields:
                fd = self.get_region_field_data(field)

                # Average the data for the region
                if ed.average_mode == 'arthimetic':
                    fd.arthimetic_average()
                elif ed.average_mode == 'volume':
                    fd.volume_average(fd_ivol)
                elif ed.average_mode == 'area-weighted':
                    coordinates = [node.coordinates for nodes in self.region.nodes for node in nodes]
                    fd.axisymmetric_area_weight(coordinates)
                elif ed.average_mode == 'none':
                    fd.avg = fd.data
                    fd.std = np.zeros(shape=fd.avg.shape)

                extracted_data.append(fd)
        return extracted_data
    
class OutputWriter():

    def __init__(self, odb_extractor, extracted_data, output_dir=None, prefix="odbex"):
        # type: (OdbExtractor, list[FieldData], str, str) -> None
        self.odb_name = os.path.splitext(os.path.basename(odb_extractor.odb.name))[0]
        self.extracted_data = extracted_data
        if output_dir is None:
            self.output_dir = os.path.dirname(odb_extractor.odb.name)
        else:
            self.output_dir = output_dir
        self.prefix = prefix
        self.set_output_name()

    def set_output_name(self):
        self.output_name = "_".join([self.prefix, self.odb_name])

    def write_npz(self):
        # type: () -> None
        # Create a dictionary of the data to be written to file
        data_asdict = {}
        for ed in self.extracted_data:
            data_asdict.update(
                {
                    '|'.join([ed.id, 'components']): ed.components,
                    '|'.join([ed.id, "data"]): np.stack([ed.avg, ed.std])
                }
            )

        # Create output filepath and save as npz file
        output_fp = os.path.join(self.output_dir, self.output_name + ".npz")
        np.savez(output_fp, **data_asdict)
        print('wrote extracted data to file -> {}'.format(output_fp))

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

def extract_from_odb(odb_fp, odbex_cfg_fp, write_mode='numpy', output_dir=None):
    # type: (str, str, str) -> None
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

    # Create writer and write to requested filetype
    writer = OutputWriter(odbex, extracted_data, output_dir)
    if write_mode == 'numpy':
        writer.write_npz()
    
    # Close odb
    odbex.close_odb()
