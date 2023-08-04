import os, json

import numpy as np

import pc2abaqus as pc

TEST_ODB_FILEPATH = "test_2fiber_RUC_u23.odb"
                                 
def _test_filepath():
    return os.path.join(os.path.dirname(__file__), TEST_ODB_FILEPATH)

def main():
    odb_handler = pc.extract.OdbHandler(_test_filepath())
    
    instance_name = odb_handler.instance_names[0]
    instance = odb_handler.get_instance_by_name(instance_name)
    subset = odb_handler.get_mesh_items_by_number("node", instance, [1, 2, 3])
    subset = odb_handler.get_mesh_items_by_set("element", instance, ["set-composite"], ignorecase=True)
    
    res = {}
    
    for step in odb_handler.analysis_steps:
        
        step_dict = {step.name: {}}
        res.update(step_dict)
            
        frames = odb_handler.slice_step_frames(step.frames, num_frames=4)
        frame_timevals = odb_handler.get_frame_timevals(frames)
        for ss in subset:
            
            ss_dict = {ss.name: {}}
            step_dict[step.name].update(ss_dict)
            # step_dict[step.name].update({ss.name: {}})
            
            iptv = odb_handler.get_integration_point_volumes(frames, ss)            
            for field in ["S", "E"]:
                
                fd = pc.extract.FieldDataHandler(field, ss, frames)
                fd.extract()
                fd.volume_average_field(iptv)


                ss_dict[ss.name].update({field: fd.data_to_records(frame_timevals)})

    odb_handler.odb.close()
    
    with open("test.json", "w") as f:
        json.dump(res, f, indent=4)

if __name__ == "__main__":
    main()