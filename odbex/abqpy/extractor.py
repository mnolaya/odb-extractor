import os
import json

import numpy as np

from odbAccess import openOdb

import abqpy

TEST_OUT = 'test_odb_py2_output.json'

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

def get_extraction_regions(odb, extraction_defintions):
    regions = []
    for ed in extraction_defintions:
        instance = odb.rootAssembly.instances[ed['instance']]
        if ed['type'].lower() == 'element':
            regions.append(get_instance_element_set(instance, ed['id']))
        elif ed['type'].lower() == 'node':
            regions.append(get_instance_node_set(instance, ed['id']))
        else:
            print('incorrect region type chosen: {}'.format(ed['type']))
            print('please select either "element" or "node"')
            print('terminating...')
            exit() 
    return regions

def extract(odb_filepath, odbex_cfg):
    # type: (str, str) -> None

    # Open the odb
    odb = openOdb(odb_filepath)
    print('extracting requested field data from {}'.format(odb_filepath))

    # Get the regions data is to be extracted on
    extraction_regions = get_extraction_regions(odb, odbex_cfg['extract'])

    # Extract data from odb into a dictionary
    odb_data = {}
    for step_name, step in odb.steps.items():
        # Get evenly spaced slice of frames
        frames = slice_frames_evenly(step.frames, num_frames=odbex_cfg['nframes'])

        # Initialize dictionaries to store extracted data in
        field_data_dicts = {ed['id']: {f: {'data': []} for f in ed['fields']}for ed in odbex_cfg['extract']}

        # Create a dictionary to store the step data
        step_data = {'increments': {f.frameId: f.frameValue for f in frames}, 'field_data': field_data_dicts}

        # Extract data for each frame 
        for i, frame in enumerate(frames):
            print('extracting data on increment frame {} of {}'.format(i+1, len(frames)))
            for region, ed in zip(extraction_regions, odbex_cfg['extract']):
                for field_name in ed['fields']:
                    # Get all field output for current field and frame
                    field_output = frame.fieldOutputs[field_name]

                    # Get the field data dictionary to be updated with extracted data for this field, frame
                    field_dict = field_data_dicts[ed['id']][field_name]

                    # Add component labels to the dict if not already present
                    if 'components' not in field_dict.keys():
                        components = list(field_output.componentLabels)
                        if not components: components = [field_name]
                        field_dict.update({'components': components})

                    # Use the bulkDataBlocks method to retrieve all field output data for the region
                    bdbs = field_output.getSubset(region=region).bulkDataBlocks
                    if not bdbs: continue

                    # Stack data into a single array and convert to list for future json serialization
                    data = np.vstack(bdb.data for bdb in bdbs).tolist()

                    # Get element and integration point numbering if not already present and element region type
                    if ed['type'].lower() == 'element' and 'ips' not in field_data_dicts[ed['id']].keys():
                        elems = np.hstack(bdb.elementLabels for bdb in bdbs).tolist()
                        ips = np.hstack(bdb.integrationPoints for bdb in bdbs).tolist()
                        field_data_dicts[ed['id']].update({'ips': ips, 'elems': elems})

                    # Get node numbering if not already present and node region type
                    if ed['type'].lower() == 'node' and 'nodes' not in field_data_dicts[ed['id']].keys():
                        nodes = np.hstack(bdb.nodeLabels for bdb in bdbs).tolist()
                        field_data_dicts[ed['id']].update({'nodes': nodes})
                    
                    # Append the field data for this frame to the field data dictionary
                    field_dict['data'].append(data)

        # Update the odb data dictionary with the data for the current step
        odb_data.update({step_name: step_data})

    # Write raw output data to file
    output_filename = '_'.join(['extracted', os.path.splitext(os.path.basename(odb_filepath))[0]]) + '.json'
    output_filepath = os.path.join(odbex_cfg['export'], 'raw_odbex', output_filename)
    with open(output_filepath, 'w+') as f:
        json.dump(odb_data, f, indent=4)
        print('requested field data from {} successfully written to file: {}'.format(odb_filepath, output_filepath))