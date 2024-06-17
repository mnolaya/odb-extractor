import pathlib
import json

from attrs import define, field, evolve
import numpy as np

@define
class FieldData:
    step: str
    region: str
    increments: dict[int, float]
    field: str
    data: np.ndarray
    components: list[str]

    @classmethod
    def from_dict(cls, step: str, region: str, increments: dict[int, float], field: str, field_data_dict: dict[str, list]):
        data = cls._load_field_data(field_data_dict['data'])
        components = field_data_dict['components']
        return cls(step, region, field, increments, data, components)

    @staticmethod
    def _load_field_data(field_data: dict) -> np.ndarray:
        return np.array([d for d in field_data])

@define
class RegionData:
    region: str
    field_data: dict[str, FieldData] = field(factory=dict)

    # Volume average data for specified on a region.
    def volume_average_field(self, field: str) -> np.ndarray:
        if 'IVOL' not in self.field_data.keys():
            print('error: IVOL was not found in the available field data for the region')
            print('ensure IVOL is requested for simulation field outputs and in the odbex config file when extracting data')
            return
        field_data = self.field_data[field].data
        ipvol = self.field_data['IVOL'].data
        vol_averaged = np.array([np.sum(fd*ipv, axis=0)/np.sum(ipv) for fd, ipv in zip(field_data, ipvol)])
        return evolve(self.field_data[field], data=vol_averaged)

@define
class StepData:
    step: str
    region_data: dict[str, RegionData] = field(factory=dict)
    
@define
class SimulationData:
    step_data: dict[str, StepData] = field(factory=dict)

    @classmethod
    def from_extracted(cls, data_filepath: pathlib.Path):
        # Initialize
        cls_ = cls()

        # Load raw data from json
        with open(data_filepath, 'r') as f:
            raw_data = json.load(f)

        # Update dictionary of step data with StepData/RegionData/FieldData objects
        for step, step_data in raw_data.items():
            sd = StepData(step)
            increments = step_data['increments']
            for region, field_data_dicts in step_data['field_data'].items():
                sd.region_data.update({region: RegionData(
                    region=region,
                    field_data={field: FieldData.from_dict(
                        step, region, increments, field, fdd
                    ) for field, fdd in field_data_dicts.items() if not field.lower() in ['elems', 'ips', 'nodes']}
                )})
            cls_.step_data.update({step: sd})
        return cls_
    
    # Return a RegionData object for the specified step and region.
    def get_region_data(self, step: str, region: str) -> RegionData:
        return self.step_data[step].region_data[region]

    # Return a FieldData object for the specified step, region, and field.
    def get_field_data(self, step: str, region: str, field: str) -> FieldData:
        return self.get_region_data(step, region).field_data[field]