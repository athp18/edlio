"""
Wrapper to automatically convert Syntalos EDL-style data to MoSeq data. MoSeq file structure:
- base_dir
  - depth.avi (depth vid)
  - depth_ts.txt (timestamps file)
  - metadata.json (metadata file)

Ideally the user can just do:
> from edlio.format import format
> format()
"""

import os
import tomlkit
from .unit import EDLError
import re

def generate_metadata():
  pass
  return metadata_dict

def _detect_edl_type(path):
    if not os.path.isdir(path):
        raise EDLError(f"The path '{path}' is not a directory.")

    manifest_path = os.path.join(path, 'manifest.toml')
    if not os.path.isfile(manifest_path):
        raise EDLError(f"No manifest.toml file found in '{path}'.")

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = tomlkit.load(f)
    except tomlkit.exceptions.TOMLKitError as e:
        raise EDLError(f"Error parsing manifest.toml: {str(e)}")

    edl_type = manifest.get('type')
    if edl_type == 'dataset':
        return 'EDLDataset'
    elif edl_type == 'group':
        return 'EDLGroup'
    elif edl_type == 'collection':
        return 'EDLCollection'
    elif edl_type:  # Generic EDLUnit
        return 'EDLUnit'
    else:
        raise EDLTypeError(f"Unknown or invalid EDL type in manifest: {edl_type}")
    
def dump_timestamps(dset, output='depth_ts.txt', as_float=True):
    """
    Simple function to dump timestamps to a .txt file for easy analysis. Timestamps are converted to a float.

    Args:
    dset: EDLDataset that contains Frame objects
    output (string): txt file to dump timestamps to
    as_float (bool): whether to save the timestamps at floats (default: string)
    """
    with open(output, 'w') as f:
        for frame in dset.read_data():
            timestamp = str(frame.time)
            numeric = re.search(r'(\d+\.\d+)', timestamp)
            if numeric:
                if as_float:
                    float_timestamp = float(numeric.group(1))
                    f.write(f'{float_timestamp}\n')
                else:
                    f.write(f'{numeric.group(1)}\n')
    print(f'Timestamps saved to {output}')

def format(path=os.getcwd()):
  type = _detect_edl_type(path)
  if type == 'EDLCollection':
    dcoll = edlio.load(path)
    dset = dcoll.group_by_name('videos').dataset_by_name('orbbec-depth-sensor')
    input_dir, input_filename = os.path.split(path)
    input_name, input_ext = os.path.splitext(input_filename)
    tstamps_path = os.path.join(input_dir, tstamps_path, 'depth_ts.txt')
    
    timestamps = dump_timestamps(dset, tstamps_path)
  elif type == 'EDLDataset':
    pass
  elif type == 'EDLGroup':
    pass
    
    
    
    
