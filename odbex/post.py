import pathlib
# import orjson

import attrs
import numpy as np

# @define
# class FieldData:
#     step: str
#     region: str
#     field: str
#     data: np.ndarray
#     std: np.ndarray
#     components: list[str] | None

#     @classmethod
#     def from_dict(cls, step: str, region: str, field: str, field_data_dict: dict[str, list]):
#         data = cls._load_field_data(field_data_dict['data'])
#         std = cls._load_field_data(field_data_dict['std'])
#         if 'components' in field_data_dict.keys():
#             components = field_data_dict['components']
#         else:
#             components = None
#         return cls(step, region, field, data, std, components)

#     @staticmethod
#     def _load_field_data(field_data: dict) -> np.ndarray:
#         return np.array([d for d in field_data])

# @define
# class RegionData:
#     region: str
#     field_data: dict[str, FieldData] = field(factory=dict)

#     # # Volume average data for specified field on a region.
#     # def volume_average_field(self, field: str) -> np.ndarray:
#     #     if 'IVOL' not in self.field_data.keys():
#     #         print('error: IVOL was not found in the available field data for the region')
#     #         print('ensure IVOL is requested for simulation field outputs and in the odbex config file when extracting data')
#     #         return
#     #     field_data = self.field_data[field].data
#     #     ipvol = self.field_data['IVOL'].data
#     #     vol_averaged = np.array([np.sum(fd*ipv, axis=0)/np.sum(ipv) for fd, ipv in zip(field_data, ipvol)])
#     #     return evolve(self.field_data[field], data=vol_averaged)

#     # # Average data for specified field on a region.
#     # def average_field(self, field: str) -> np.ndarray:
#     #     field_data = self.field_data[field].data
#     #     averaged = np.array([np.mean(fd, axis=0) for fd in field_data])
#     #     return evolve(self.field_data[field], data=averaged)

#     # # Return a FieldData object for the specified step, region, and field.
#     # def get_field_data(self, field: str) -> FieldData:
#     #     return self.field_data[field]

# @define
# class StepData:
#     step: str
#     increments: dict[int, float]
#     region_data: dict[str, RegionData] = field(factory=dict)
    
# @define
# class SimulationData:
#     step_data: dict[str, StepData] = field(factory=dict)

#     @classmethod
#     def from_raw_extracted(cls, data_filepath: pathlib.Path):
#         # Initialize
#         cls_ = cls()

#         # Load raw data from json
#         with open(data_filepath, 'r') as f:
#             raw_data = orjson.loads(f.read())

#         # Update dictionary of step data with StepData/RegionData/FieldData objects
#         for step, step_data in raw_data.items():
#             increments = step_data['increments']
#             sd = StepData(step, increments)
#             for region, field_data_dicts in step_data['field_data'].items():
#                 sd.region_data.update({region: RegionData(
#                     region=region,
#                     field_data={field: FieldData.from_dict(
#                         step, region, field, fdd
#                     ) for field, fdd in field_data_dicts.items() if not field.lower() in ['elems', 'ips', 'nodes']}
#                 )})
#             cls_.step_data.update({step: sd})
#         return cls_
    
#     # Return a dictionary of the increments associated with the field data
#     def get_increments(self, step: str) -> dict[int, float]:
#         return self.step_data[step].increments

#     # Get times associated with frames in a step associated with as step    
#     def get_step_frame_times(self, step: str) -> np.ndarray:
#         return np.array(sorted(self.step_data[step].increments.values()))
    
#     # Return a RegionData object for the specified step and region.
#     def get_region_data(self, step: str, region: str) -> RegionData:
#         return self.step_data[step].region_data[region]
    
#     # All available regions for each step
#     @property
#     def regions(self):
#         return {sd.step: [region for region in sd.region_data.keys()] for sd in self.step_data.values()}
    
@attrs.define
class OdbexData:

    filepath: pathlib.Path
    steps: list[str] = attrs.field(init=False)
    regions: list[str] = attrs.field(init=False)
    fields: dict[str, list[str]] = attrs.field(init=False)
    data: dict[str, np.ndarray] = attrs.field(init=False, repr=False)
    region: str = attrs.field(init=False)
    mesh_type: str = attrs.field(init=False)
    step: str = attrs.field(init=False)
    field: str = attrs.field(init=False)
    _data_key: str = attrs.field(init=False)

    def __attrs_post_init__(self):
        self._load_npz()
        self._get_step_names()
        self._get_regions()
        self._get_field_names()

    def _set_data_key(self):
        self._data_key = "|".join([self.step, self.region, self.mesh_type, self.field])

    def get_field_data(self, field: str | None = None) -> tuple[np.ndarray, list[str]]:
        if type(field) == str:
            self.set_field(field)
        self._set_data_key()
        return self.data["|".join([self._data_key, 'data'])], self.data["|".join([self._data_key, 'components'])]

    def set_region(self, region: str, mesh_type: str):
        self.region = region
        self.mesh_type = mesh_type

    def set_field(self, field: str):
        self.field = field

    def set_step(self, step: str):
        self.step = step

    def _load_npz(self):
        import warnings
        data = np.load(self.filepath)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message="Reading `.npy` or `.npz` file required additional header parsing", category=UserWarning)
            np.savez(self.filepath, **data)
        data.close()
        with np.load(self.filepath, mmap_mode='r') as data:
            self.data = {k: arr.copy() for k, arr in data.items()}

    def _get_step_names(self):
        self.steps = []
        for key in self.data.keys():
            key_components = key.split('|')
            step_name = key_components[0]
            if step_name not in self.steps: self.steps.append(step_name)

    def _get_regions(self):
        self.regions = []
        for key in self.data.keys():
            key_components = key.split('|')
            region = '|'.join(key_components[1:4])
            if region not in self.regions: self.regions.append(region)

    def _get_field_names(self):
        self.fields = {}
        for key in self.data.keys():
            key_components = key.split('|')
            region = '|'.join(key_components[1:4])
            field = key_components[4]
            if field not in self.fields.keys(): 
                self.fields.update({field: [region]})
            else:
                self.fields[field].append(region)