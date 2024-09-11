"""
Wrapper to automatically convert Syntalos EDL-style data to MoSeq data. MoSeq file structure:
- base_dir
  - depth.avi (depth vid)
  - depth_ts.txt (timestamps file)
  - metadata.json (metadata file)
"""

import os
import tomlkit
from .unit import EDLError
import re
import subprocess

def generate_metadata(file, subjectname, session_name, start_time, depth_resolution=[640,576], color_resolution=[640,576], little_endian=True):
  pass
  return metadata_dict

def encode_video(input_path, output_filename="depth.avi", fps=30, pixel_format="gray16", codec="ffv1", threads=6, crf=10, slices=24, slicecrc=1):
    input_dir, input_filename = os.path.split(input_path)
    input_name, input_ext = os.path.splitext(input_filename)
    output_path = os.path.join(input_dir, output_filename)
  
    probe_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-count_packets",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        input_path
    ]
    
    try:
        probe_output = subprocess.check_output(probe_command, universal_newlines=True)
        width, height = map(int, probe_output.strip().split(','))
    except subprocess.CalledProcessError as e:
        print(f"Error probing video: {e}")
        return None

    frame_size = f"{width}x{height}"
    command = [
        "ffmpeg",
        "-i", input_path,
        "-y",
        "-loglevel", "fatal",
        "-an",
        "-crf", str(crf),
        "-vcodec", codec,
        "-preset", "ultrafast",
        "-threads", str(threads),
        "-slices", str(slices),
        "-slicecrc", str(slicecrc),
        "-r", str(fps),
        "-pix_fmt", pixel_format,
        "-s", frame_size,
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Video encoded successfully. Output saved as {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during video encoding. FFmpeg returned code {e.returncode}")
        print("Error output:")
        print(e.stderr)
    except FileNotFoundError:
        print("FFmpeg not found. Please ensure FFmpeg is installed and added to your system PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    
    return None

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
  generate_metadata()
  encode_video(path)
    
    
    
    
