import os
import json

import numpy as np

from odbAccess import openOdb
import abaqusConstants as abqconst

import abqpy

TEST_OUT = 'test_odb_py2_output.json'

def extract(odb_filepath, odbex_cfg):
    # type: (str, dict) -> None

    # Open the odb
    odb = openOdb(odb_filepath)
    print('extracting requested field data from {}'.format(odb_filepath))

    # print(odb.rootAssembly.instances.values()[0].nodeSets)
    # print(odb.rootAssembly.instances.values()[0].elementSets)
    # exit()

    # Get the regions data is to be extracted on
    extraction_regions = build_extraction_region_dict(odb, odbex_cfg['extract'])
    


    # Extract data from odb into a dictionary
    extracted_odb_data = {}

    for step_name, step in odb.steps.items():
        step_data = extract_step(step, odbex_cfg['nframes'], extraction_regions)

        # Update the odb data dictionary with the data for the current step
        extracted_odb_data.update({step_name: step_data})

    # Write raw output data to file
    prefix = odbex_cfg['export_prefix']
    if prefix is None: prefix = 'odbex'
    output_filename = '_'.join([prefix, os.path.splitext(os.path.basename(odb_filepath))[0]]) + '.json'
    output_dir = os.path.join(os.path.dirname(odb_filepath))
    if output_dir == '': output_dir = '.'
    output_filepath = os.path.join(output_dir, output_filename)
    if not os.path.exists(output_dir): os.mkdir(output_dir)
    with open(output_filepath, 'w+') as f:
        json.dump(extracted_odb_data, f, indent=4)
        print('requested field data from {} successfully written to file: {}'.format(odb_filepath, output_filepath))

def slice_frames_evenly(frames, num_frames=None):
    # type: (int, int | None) -> list[OdbFrame]
    
    # Check if number of frames is provided or if it exceeds the number of available frames 
    total_frames = len(frames)
    if num_frames >= total_frames or num_frames is None: return frames
    
    # Create evenly spaced slice indices
    # Ensure that the last frame is always included
    indices = list(np.arange(0, total_frames, round(total_frames/num_frames), dtype=int))
    if indices[-1] != total_frames-1: indices.append(total_frames-1)
    return [frames[i] for i in indices]

def get_instance_element_set(instance, name):
    # type: (OdbInstance, str) -> OdbSet
    return instance.elementSets[name]

def get_instance_node_set(instance, name):
    # type: (OdbInstance, str) -> OdbSet
    return instance.nodeSets[name]

def _make_number_slice(numbers):
    # type: (list) -> np.ndarray:
    '''
    Convert a list of element/node numbers into an array for slicing.
    If the list contains a string, the strings can be of a single integer (e.g., "1") or
    a range of integers in the form "START-STOP" (e.g., "1-10").
    '''
    nums = []
    for n in numbers:
        if type(n) == int: nums.append(n)  # Subtract 1 to get correct index
        if type(n) == str:
            if '-' in n:  # Range of values
                start, stop = n.split('-')
                nums += np.arange(int(start), int(stop) + 1).tolist()
            else: nums.append(int(n))  # Convert string to int and subtract 1 to get correct index
    return np.unique(nums)

def get_instance_elements_by_number(instance, numbers):
    # type: (OdbInstance, list) -> list[OdbMeshElement]
    '''
    Get an array of elements on the instance.
    The list of element numbers can be integers or strings.
    If the list contains a string, the strings can be of a single integer (e.g., "1") or
    a range of integers in the form "START-STOP" (e.g., "1-10").
    '''
    elems = []
    for n in _make_number_slice(numbers):
        elems.append(instance.getElementFromLabel(n))
    return np.array(elems)

    # return np.array(instance.elements)[_make_number_slice(numbers)]

def get_instance_nodes_by_number(instance, numbers):
    # type: (OdbInstance, list) -> list[OdbMeshNode]
    '''
    Get an array of nodes on the instance.
    The list of node numbers can be integers or strings.
    If the list contains a string, the strings can be of a single integer (e.g., "1") or
    a range of integers in the form "START-STOP" (e.g., "1-10").
    '''
    nodes = []
    for n in _make_number_slice(numbers):
        nodes.append(instance.getNodeFromLabel(n))
    return np.array(nodes)

def build_extraction_region_dict(odb, extraction_defintions):
    _region_getters = {
        'element': {
            'set': get_instance_element_set,
            'number': get_instance_elements_by_number,
        },
        'node': {
            'set': get_instance_node_set,
            'number': get_instance_nodes_by_number,
        },
    }
    _mesh_number_prefix = {'element': 'E', 'node': 'N'}
    
    regions = {}
    for ed in extraction_defintions:
        rmesh, rtype, rid, fields = ed['mesh'].lower(), ed['type'].lower(), ed['id'], ed['fields']
        try:
            instance = odb.rootAssembly.instances[ed['instance']]
        except KeyError:
            print('error: instance {} does not exist'.format(ed['instance']))
            print('the instances on the model which field data can be extracted from are:')
            for inst in odb.rootAssembly.instances.keys():
                print('-> {}'.format(inst))
            print('terminating...')
            exit()
        try:
            rg = _region_getters[rmesh][rtype]
        except KeyError:
            print('incorrect value entry for region "type" ({}) or "get" ({})'.format(ed['type'], ed['get']))
            print('valid type values: node, element')
            print('valid get values: set, number')
            print('terminating...')
            exit()
        region = rg(instance, rid)
        if rtype == 'set':
            regions.update({rid: {'region': region, 'fields': fields}})
        else:
            pfx = _mesh_number_prefix[rmesh]
            regions.update({'{}{}'.format(pfx, mesh_item.label): {'region': mesh_item, 'fields': fields} for mesh_item in region})
    return regions

def get_field_data(field_name, frame, region):
    # type: (str, odb.Frame, odb.Region) -> tuple[np.ndarray, list[str]]

    # Get all field output for current field and frame
    field_output = frame.fieldOutputs[field_name]

    # Get component labels for the field
    components = list(field_output.componentLabels)
    if not components: components = [field_name]

    # Use the bulkDataBlocks method to retrieve all field output data for the region
    bdbs = field_output.getSubset(region=region).bulkDataBlocks
    check_node = str(type(region)) == "<type 'OdbMeshNode'>"
    if field_name in ['S', 'E', 'LE'] and check_node:
        bdbs = field_output.getSubset(region=region, position=abqconst.ELEMENT_NODAL).bulkDataBlocks
    
    # Stack data into numpy array
    data = np.vstack(bdb.data for bdb in bdbs)

    # Get max. principal if stress or strain requested
    if field_name in ['S', 'E', 'LE'] and not check_node:
        bdbs = field_output.getSubset(region=region).getScalarField(invariant=abqconst.MAX_PRINCIPAL).bulkDataBlocks
        data = np.hstack([data, np.vstack(bdb.data for bdb in bdbs)])
        components += ("{}MAXPRINC".format(field_name), )
    return data, components

# def vol_average_field_data(field_data, ipvols):
#     # type: (np.ndarray, np.ndarray) -> np.ndarray
#     return np.sum(field_data*ipvols, axis=0)/np.sum(ipvols)

def average_field_data(field_data, ivols=None):
    # type: (np.ndarray, np.ndarray | None) -> tuple[np.ndarray]
    # Non-integration point quantity, or no integration point volumes passed
    if ivols is None or field_data.shape[0] != ivols.shape[0]:
        return np.mean(field_data, axis=0), np.std(field_data, axis=0)
    # Volume-average if integration point quantity
    else:
        return np.sum(field_data*ivols, axis=0)/np.sum(ivols), np.std(field_data*ivols, axis=0)
    
def update_field_dict(field_dict, data_mean, data_std, components):
    # type: (dict, np.ndarray, list[str]) -> None
    field_dict['data'].append(data_mean.tolist())
    field_dict['std'].append(data_std.tolist())
    if 'components' not in field_dict.keys(): field_dict.update({'components': components})

def extract_step(step, num_frames, extraction_regions):
    # type: (Odb.Step, int, dict) -> dict

    # Get evenly spaced slice of frames
    frames = slice_frames_evenly(step.frames, num_frames=num_frames)

    # Initialize dictionaries to store extracted data in
    field_data_dicts = {k: {f: {'data': [], 'std': []} for f in v['fields']} for k, v in extraction_regions.items()}

    # Create a dictionary to store the step data
    step_data = {'increments': {f.frameId: f.frameValue for f in frames}, 'field_data': field_data_dicts}

    # Extract data for each frame 
    for i, frame in enumerate(frames):
        print('extracting data for increment {} (frame {} of {})'.format(frame.frameId, i+1, len(frames)))
        # for region, ed in zip(extraction_regions, odbex_cfg['extract']):
        for rid, fdd in field_data_dicts.items():
            # Set the region for field data extraction
            region = extraction_regions[rid]['region']

            # Get integration point volumes first for volume-averaging quantities
            ivols = None
            if 'IVOL' in fdd.keys(): 
                ivols, components = get_field_data('IVOL', frame, region)
                # update_field_dict(fdd['IVOL'], ivols, components)
                # field_data_dicts[ed['id']]['IVOL']['data'].append(ivols)
            
            # Loop through field data labels and get bulk data, then average for the region
            for field_name, field_dict in fdd.items():
                if field_name == 'IVOL': continue

                # Get field data and average/volume average as appropriate
                try:
                    fd, components = get_field_data(field_name, frame, region)
                except KeyError as e:
                    print('warning: field {} not available for extraction in current ODB. continuing to next requested field or odb...'.format(field_name))
                    continue
                fd_mean, fd_std = average_field_data(fd, ivols)

                # Update the field dict
                update_field_dict(field_dict, fd_mean, fd_std, components)
    return step_data

if __name__ == '__main__':
    TEST_CFG = {
        "file_explorer": {
            "enable": True,
            "starting_directory": "C:/some/dir"
        },
        "odb_filepaths": [
            "C:/some/dir/analysis.odb"
        ],
        "odb_root": "C:/some/dir",
        "extract": [
            {
                "instance": "MATRIX-1",
                "mesh": "element",
                "type": "set",
                "id": "SET-ALLELEMENTS",
                "fields": ["S", "E", "IVOL", "TEMP"]
            },
            # {
            #     "instance": "MATRIX-1",
            #     "mesh": "element",
            #     "type": "number",
            #     "id": [1, 2, 3, "3", "4-9"],
            #     "fields": ["S", "E", "IVOL", "TEMP"]
            # },
            # {
            #     "instance": "MATRIX-1",
            #     "type": "element",
            #     "get": "number",
            #     "id": 1,
            #     # "fields": ["S", "E", "IVOL", "TEMP"]
            # },
            # {
            #     "instance": "MICROSTRUCTURE-1",
            #     "type": "element",
            #     "id": "SET-MATRIX",
            #     "fields": ["S", "E", "IVOL", "TEMP", "SDV1", "SDV2", "SDV3", "SDV4", "SDV5", "SDV6", "SDV7"]
            # }
        ],
        "nframes": None,
        "export": "."
    }
    TEST_ODB = '/work/pi_marianna_maiaru_uml_edu/michael_olaya/tests/process_model/damage_during_cure/work/9elem_composite_cure_perm2_4cpu.odb'
    extract(TEST_ODB, TEST_CFG)