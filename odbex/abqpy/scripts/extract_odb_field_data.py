import os, argparse, json, glob

import odbex as oex

def _get_config(config_filepath):
    # type: (str | None)  -> dict
    if config_filepath is None:
        config_filepath = os.path.join(os.getcwd(), "extractor_config.json")
    return oex._json.json_load(config_filepath)

def _get_odb_filepaths(config):
    # type: (dict[str, str | float | bool | None]) -> list[str]
    if config["odb_root"] is not None:
        return glob.glob(os.path.join(config["odb_root"], "*.odb"))
    elif config["odb_filepaths"] is not None:
        return config["odb_filepaths"]
    else:
        return oex._explorer.filepaths_from_odb_explorer(config["file_explorer"]["starting_directory"])
    
def _get_model_region(odb_handler, field_request):
    # type: (oex.exract.OdbHandler, oex.extract.FieldRequest) -> OdbAssembly | OdbInstance
    if field_request.region_type.lower() == "instance":
        model_region = odb_handler.get_instance_by_name(field_request.region_name)
    else:
        model_region = odb_handler.assembly
    return model_region

def _get_region_subsets(odb_handler, field_request, model_region):
    # type: (oex.exract.OdbHandler, oex.extract.FieldRequest, OdbAssembly | OdbInstance) -> list[OdbMeshNode | OdbMeshElement | OdbSet]
    mesh_nums, mesh_sets = [id for id in field_request.mesh_ids if type(id) == int], [id for id in field_request.mesh_ids if type(id) == str]
    region_subsets = odb_handler.get_mesh_items_by_number(field_request.mesh_type, model_region, mesh_nums)
    region_subsets += odb_handler.get_mesh_items_by_set(field_request.mesh_type, model_region, mesh_sets)
    return region_subsets

def _export_extracted_data(extracted, file_basename, directory=None, prefix="extracted"):
    # type: (dict, str, str | None, str) -> None
    if directory is None: directory = os.getcwd()
    filepath = os.path.join(directory, "_".join([prefix, file_basename + ".json"]))
    print("*Field data from {}.odb successfully extracted!\nExporting to: {}\n---\n".format(file_basename, filepath))
    with open(filepath, "w") as f:
        json.dump(extracted, f, indent=4)    

def _get_integration_point_volumes(odb_handler, frames, mesh_subset):
    # type: (oex.extract.OdbHandler, list[OdbFrame], oex.extract.MeshSubset) -> list[np.ndarray] | None
    ipt_vols = None
    if mesh_subset.type == "element":
        ipt_vols = odb_handler.get_integration_point_volumes(frames, mesh_subset.mesh)
    return ipt_vols

def _get_frames(odb_handler, analysis_step, num_frames):
    # type: (oex.extract.OdbHandler, OdbStep, int | None) -> tuple[list[OdbFrame], list[float]]
    frames = odb_handler.slice_step_frames(analysis_step.frames, num_frames=num_frames)
    frame_timevals = odb_handler.get_frame_timevals(frames)
    return frames, frame_timevals

def _set_subset_key(mesh_subset):
    # type: (oex.extract.MeshSubset) -> str
    subset_key = mesh_subset.id
    if type(subset_key) == int: subset_key = "{}{}".format(mesh_subset.type[0].upper(), subset_key)
    return subset_key

def _extract_fields_from_subset(mesh_subset, field_vars, frames, frame_timevals, ipt_vols=None):
    # type: (oex.extract.MeshSubset, list[str], list[OdbFrame], list[float], list[np.ndarray]) -> dict[str, list[dict[str, float]]]
    field_data_dicts = {}
    for field in field_vars:
        fde = oex.extract.FieldDataExtractor(mesh_subset.mesh, field, frames)
        fde.extract(ipt_vols=ipt_vols)
        field_data_dicts.update({field: fde.data_to_records(frame_timevals)})
        print("Data for field var {} on the current subset sucessfully extracted".format(field))
    return field_data_dicts

def _update_step_dict_with_field_data(step_dict, subset_key, field_data_dicts):
    # type: (dict, str, dict[str, list[dict[str, float]]]) -> None
    step_dict.update({subset_key: {k: v for k, v in field_data_dicts.items()}})
    
def _request_field_data(odb_handler, frames, frame_timevals, analysis_step, extraction_dict, field_requests):
    # type: (oex.extract.OdbHandler, list[OdbFrame], list[int], OdbStep, dict, list[oex.extract.FieldRequest]) -> None
    for fr in field_requests:
        ipt_vols = _get_integration_point_volumes(odb_handler, frames, fr.mesh_subset)
        subset_key = _set_subset_key(fr.mesh_subset)
        print("Extracting fields on model subset {}...".format(subset_key))
        field_data_dicts = _extract_fields_from_subset(fr.mesh_subset, fr.field_vars, frames, frame_timevals, ipt_vols)          
        _update_step_dict_with_field_data(extraction_dict[analysis_step.name], subset_key, field_data_dicts)

def _extract_from_odb(filepath, config_field_requests, num_frames=None):
    # type: (str, list[dict[str, str | list]], int | None) -> dict
    odb_handler = oex.extract.OdbHandler(filepath)
    field_requests = oex.extract.field_requests_from_config(config_field_requests, odb_handler)
    extraction_dict = {}
    for step in odb_handler.analysis_steps:
        extraction_dict.update({step.name: {}})
        frames, frame_timevals = _get_frames(odb_handler, step, num_frames)
        _request_field_data(odb_handler, frames, frame_timevals, step, extraction_dict, field_requests)
    return extraction_dict

def main(args):
    # type: (argparse.ArgumentParser) -> None
    cfg = _get_config(args.config)
    for fp in _get_odb_filepaths(cfg):
        print("**Extracting field data from {}...".format(fp))
        file_basename = os.path.splitext(os.path.basename(fp))[0]
        extracted = _extract_from_odb(fp, cfg["field_requests"], cfg["slice_frames_by"])
        _export_extracted_data(extracted, file_basename, **cfg["export"])