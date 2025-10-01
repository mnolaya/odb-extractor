# import os
# import json
# import sys

# import numpy as np

# from odbAccess import openOdb
# import abaqusConstants as abqconst

from odbex.abqpy.extractor import ExtractionDefinition

# def _make_number_slice(numbers):
#     # type: (list) -> np.ndarray:
#     '''
#     Convert a list of element/node numbers into an array for slicing.
#     If the list contains a string, the strings can be of a single integer (e.g., "1") or
#     a range of integers in the form "START-STOP" (e.g., "1-10").
#     '''
#     nums = []
#     for n in numbers:
#         if type(n) == int: nums.append(n)  # Subtract 1 to get correct index
#         if type(n) == str:
#             if '-' in n:  # Range of values
#                 start, stop = n.split('-')
#                 nums += np.arange(int(start), int(stop) + 1).tolist()
#             else: nums.append(int(n))  # Convert string to int and subtract 1 to get correct index
#     return np.unique(nums)

# def get_instance_element_set(instance, name):
#     # type: (OdbInstance, str) -> OdbSet
#     return instance.elementSets[name]

# def get_instance_node_set(instance, name):
#     # type: (OdbInstance, str) -> OdbSet
#     return instance.nodeSets[name]

# def get_instance_elements_by_number(instance, numbers):
#     # type: (OdbInstance, list) -> list[OdbMeshElement]
#     '''
#     Get an array of elements on the instance.
#     The list of element numbers can be integers or strings.
#     If the list contains a string, the strings can be of a single integer (e.g., "1") or
#     a range of integers in the form "START-STOP" (e.g., "1-10").
#     '''
#     elems = []
#     for n in _make_number_slice(numbers):
#         elems.append(instance.getElementFromLabel(n))
#     return np.array(elems)

# def get_instance_nodes_by_number(instance, numbers):
#     # type: (OdbInstance, list) -> list[OdbMeshNode]
#     '''
#     Get an array of nodes on the instance.
#     The list of node numbers can be integers or strings.
#     If the list contains a string, the strings can be of a single integer (e.g., "1") or
#     a range of integers in the form "START-STOP" (e.g., "1-10").
#     '''
#     nodes = []
#     for n in _make_number_slice(numbers):
#         nodes.append(instance.getNodeFromLabel(n))
#     return np.array(nodes)

# def build_extraction_region_dict(odb, extraction_defintions):
#     _region_getters = {
#         'instance': {
#             'element': {
#                 'set': get_instance_element_set,
#                 'number': get_instance_elements_by_number,
#             },
#             'node': {
#                 'set': get_instance_node_set,
#                 'number': get_instance_nodes_by_number,
#             },
#         },
#         'assembly': {
#             'element': {
#                 'set': get_instance_element_set,
#                 'number': get_instance_elements_by_number,
#             },
#             'node': {
#                 'set': get_instance_node_set,
#                 'number': get_instance_nodes_by_number,
#             },
#         },        
#     }
#     _mesh_number_prefix = {'element': 'E', 'node': 'N'}
    
#     regions = {}
#     for ed in extraction_defintions:
#         # Temp implementation for turning off averaging for a set
#         mean_on = True
#         if 'avg' in ed.keys() and ed['avg'] == False: mean_on = False

#         rmesh, rtype, rid, fields = ed['mesh'].lower(), ed['type'].lower(), ed['id'], ed['fields']
#         if ed['subsection'] == 'assembly':
#             instance = odb.rootAssembly
#             subsection = 'assembly'
#         else:
#             try:
#                 instance = odb.rootAssembly.instances[ed['subsection']]
#                 subsection = 'instance'
#             except KeyError:
#                 print('error: instance {} does not exist'.format(ed['subsection']))
#                 print('the instances on the model which field data can be extracted from are:')
#                 for inst in odb.rootAssembly.instances.keys():
#                     print('-> {}'.format(inst))
#                 print('terminating...')
#                 exit()
#         try:
#             rg = _region_getters[subsection][rmesh][rtype]
#         except KeyError:
#             print('incorrect value entry for region "type" ({}) or "get" ({})'.format(ed['type'], ed['get']))
#             print('valid type values: node, element')
#             print('valid get values: set, number')
#             print('terminating...')
#             exit()
#         region = rg(instance, rid)
#         if rtype == 'set':
#             regions.update({rid: {'region': region, 'fields': fields, 'mean_on': mean_on}})
#         else:
#             pfx = _mesh_number_prefix[rmesh]

#             regions.update({'{}{}'.format(pfx, mesh_item.label): {'region': mesh_item, 'fields': fields, 'mean_on': mean_on} for mesh_item in region})
#     return regions

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
    print(extraction_definitions)