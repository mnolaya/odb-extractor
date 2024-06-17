import itertools, re

import numpy as np

from odbAccess import openOdb
import abaqusConstants as abqconst

def _repr(instance, class_dict):
    # type: (Any, dict) -> str
    return "{}({})".format(instance.__class__.__name__, ", ".join(["{}={}".format(attr, val) for attr, val in class_dict.items()]))

def _build_subset_definitions(config_field_request, odb_handler):
    # type: (dict, OdbHandler) -> dict
    model_region = odb_handler.get_model_region(config_field_request["region_type"], config_field_request["region_name"])
    return [
        {
            "model_region": model_region,
            "mesh_type": subset["mesh_type"],
            "mesh_id": mid,
            "field_vars": subset["fields"],
        }
        for subset in config_field_request["region_subsets"] for mid in subset["mesh_ids"]
    ]
    
def _validate_mesh_type(mesh_type):
    # type: (str) -> None 
    if mesh_type.lower() not in ["node", "element"]:
        raise SystemExit("{} is not a valid mesh type. Please choose either 'node' or 'element' as the mesh type.".format(mesh_type))

def field_requests_from_config(config_field_requests, odb_handler):
    # type: (list[dict], OdbHandler) -> list[FieldRequest]
    field_requests = []
    for cfr in config_field_requests:
        # model_region = odb_handler.get_model_region(request["region_type"], request["region_name"])
        subset_defintions = _build_subset_definitions(cfr, odb_handler)
        mesh_subsets = [MeshSubset.from_subset_definition(odb_handler=odb_handler, **sd) for sd in subset_defintions]
        field_requests += [FieldRequest(ms, sd["field_vars"]) for ms, sd in zip(mesh_subsets, subset_defintions)]
    return field_requests

class MeshSubset(object):
    __slots__ = ("mesh", "type", "id",)
    
    def __init__(self, mesh, mesh_type, mesh_id):
        # type: (list[OdbMeshNode] | list[OdbMeshElement] | OdbSet, str, str) -> None
        self.mesh = mesh
        self.type = mesh_type
        self.id = mesh_id
        
    def __repr__(self):
        # type: () -> str
        return _repr(self, {"mesh": "...", "type": self.type, "id": self.id})
        
    @classmethod
    def from_subset_definition(cls, model_region, mesh_type, mesh_id, odb_handler, **kwargs):
         # type: (OdbInstance | OdbAssembly, str, str, OdbHandler, dict) -> MeshSubset
        if type(mesh_id) == int:
            mesh_subset = odb_handler.get_mesh_items_by_label(mesh_type, model_region, mesh_id)
        else:
            mesh_subset = odb_handler.get_mesh_items_by_set_name(mesh_type, model_region, mesh_id)
        return cls(mesh_subset, mesh_type, mesh_id)
    
class FieldRequest(object):
    __slots__ = ("mesh_subset", "field_vars",)
    
    def __init__(self, mesh_subset, field_vars):
        # type: (MeshSubset, list[str]) -> FieldRequest
        self.mesh_subset = mesh_subset
        self.field_vars = field_vars
        
    def __repr__(self):
        # type: () -> str
        return _repr(self, {"mesh_subset": self.mesh_subset, "field_vars": self.field_vars})

class FieldDataExtractor:
    def __init__(self, mesh_subset, field, frames):
        # type: (list[OdbMeshNode] | list[OdbMeshElement] | OdbSet, str, list[OdbFrame]) -> FieldDataExtractor
        self.mesh_subset = mesh_subset
        self.field = field
        self.components = self._get_field_components(frames[0])
        self.frames = frames
        self.field_data = []
    
    def _get_field_components(self, ini_frame, maxprinc=True):
        # type: (OdbFrame, bool) -> tuple[str, ...]
        components = ini_frame.fieldOutputs[self.field].getSubset(region=self.mesh_subset).componentLabels
        if not components:
            components = (self.field, )
        if maxprinc and self.field in ["S", "E", "LE"]: 
            maxprinc_component = "{}MAXPRINC".format(self.field)
            components += (maxprinc_component, )
        return components  
    
    @staticmethod
    def _field_output_bdb(field_output):
        # type: (FieldOutput) -> np.ndarray
        return np.vstack(bdb.data for bdb in field_output.bulkDataBlocks)
        
    def extract(self, maxprinc=True, ipt_vols=None):
        # type: (bool, list[np.ndarray]) -> None
        for frame in self.frames:
            field_output = frame.fieldOutputs[self.field].getSubset(region=self.mesh_subset)
            field_data = self._field_output_bdb(field_output)
            if maxprinc and self.field in ["S", "E", "LE"]: 
                maxprinc_field_data = self._field_output_bdb(field_output.getScalarField(invariant=abqconst.MAX_PRINCIPAL))
                field_data = np.hstack([field_data, maxprinc_field_data])
            self.field_data.append(field_data)
        if ipt_vols is not None and len(self.field_data[0]) == len(ipt_vols[0]):
            self.volume_average_field(ipt_vols)
        else:
            self.mean_field()
            
    def mean_field(self):
        # type: () -> None
        self.field_data = [np.mean(fd, axis=1) for fd in self.field_data]        

    def volume_average_field(self, ipt_vols):
        # type: (list[np.ndarray]) -> None
        self.field_data = [np.sum(fd*iptv, axis=0)/np.sum(iptv) for fd, iptv in zip(self.field_data, ipt_vols)]
    
    def data_to_records(self, frame_timevals):
        # type: (list[float]) -> list[dict[str, float]]
        records = []
        for data, time in zip(self.field_data, frame_timevals):
            record = {"TIME": time}
            record.update({component: float(val) for component, val in zip(self.components, data)})
            records.append(record)
        return records

class OdbHandler:
    def __init__(self, odb_filepath):
        # type: (str,dict[str, str | list]) -> OdbHandler        
        self.odb_filepath = odb_filepath
        self.odb = openOdb(odb_filepath)
        self.assembly = self.odb.rootAssembly
        self.instances = [instance for instance in self.assembly.instances.values()]
        self.analysis_steps = [step for step in self.odb.steps.values()]
        
    @property
    def node_set_names(self):
        # type: () -> dict
        names = {"assembly": [nset.name for nset in self.assembly.nodeSets.values()]}
        for instance in self.instances:
            names.update({instance.name: [nset.name for nset in instance.nodeSets.values()]})
        return names
    
    @property
    def element_set_names(self):
        # type: () -> dict
        names = {"assembly": [nset.name for nset in self.assembly.elementSets.values()]}
        for instance in self.instances:
            names.update({instance.name: [nset.name for nset in instance.elementSets.values()]})
        return names
    
    @property
    def instance_names(self):
        # type: () -> list[str]
        return [instance.name for instance in self.instances]
    
    @property
    def analysis_step_names(self):
        # type: () -> list[str]
        return [step.name for step in self.analysis_steps]
    
    def get_model_region(self, region_type, region_name):
        # type: (OdbHandler, FieldRequest) -> OdbAssembly | OdbInstance
        if region_type.lower() == "instance":
            model_region = self.get_instance_by_name(region_name)
        else:
            model_region = self.assembly
        return model_region
        
    @staticmethod
    def get_frame_timevals(frames):
        # type: (list[OdbFrame]) -> list[float]
        return [f.frameValue for f in frames]
        

    def frames_by_step_num(self, step_num):
        # type: (int) -> list[OdbFrame]
        return self.analysis_steps[step_num-1].frames
        
    def slice_step_frames(self, frames, num_frames=None):
        # type: (int, int | None) -> list[OdbFrame]
        total_frames = len(frames)
        if num_frames >= total_frames or num_frames is None:
            return frames
        slice_idx = list(np.arange(0, total_frames, round(total_frames/num_frames), dtype=int))
        if slice_idx[-1] != total_frames-1: slice_idx.append(total_frames-1)
        return [frames[i] for i in slice_idx]
    
    def get_instance_by_name(self, name, ignorecase=True):
        # type: (str, bool) -> OdbInstance
        if ignorecase:
            return next(instance for instance in self.instances if re.search(name, instance.name, re.IGNORECASE) is not None)
        else:
            return self.assembly.instances[name]
        
    def get_mesh_items_by_label(self, mesh_type, model_region, label):
        # type: (str, OdbInstance | OdbAssembly, int) -> list[OdbMeshNode] or list[OdbMeshElement]
        _validate_mesh_type(mesh_type)
        return next(m for m in getattr(model_region, mesh_type + "s") if m.label == label)
        
    def get_mesh_items_by_set_name(self, mesh_type, model_region, set_name, ignorecase=True):
        # type: (str, OdbInstance | OdbAssembly, list[str], bool) -> OdbSet
        _validate_mesh_type(mesh_type)
        mesh_sets =  getattr(model_region, "{}Sets".format(mesh_type))
        if ignorecase:
            return next(mesh for key, mesh in mesh_sets.items() if re.search(key, set_name, re.IGNORECASE))
        else:
            return mesh_sets[set_name]
    
    def get_integration_point_volumes(self, frames, elements):
        # type: (list[OdbFrame], list[OdbMeshNode] | list[OdbMeshElement] | OdbSet) -> list[np.ndarray]
        iptv = []
        for frame in frames:       
            field_output = frame.fieldOutputs["IVOL"].getSubset(region=elements)
            iptv.append(FieldDataExtractor._field_output_bdb(field_output))
        return iptv
