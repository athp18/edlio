"""
Wrapper to automatically convert Syntalos EDL-style data to MoSeq data. MoSeq file structure looks like this:
- base_dir (session specific)
  - depth.avi (depth recording)
  - depth_ts.txt (depth timestamps)
  - metadata.json (session metadata)

This function assumes that you have created a recording using Syntalos' Orbbec Femto Sensor module.
"""
import os
import json
import shutil
import numpy as np
import tomlkit
from .dataio.tsyncfile import TSyncFile, LegacyTSyncFile

class FileNotFoundError(Exception):
    """Exception raised when a required file is not found."""
    pass
  
def _detect_edl_type(path: str) -> str:
    """
    Helper function to detect EDL Type and ensure that an EDLCollection is being passed to reformat

    Args:
    path (str): Path to the dataset

    Returns a string informing the dataset type
    """
    if not os.path.isdir(path):
        # ensure path is a directory and not a file
        raise FileNotFoundError(f"The path '{path}' is not a directory.")

    manifest_path = os.path.join(
        path, "manifest.toml"
    )  # the manifest.toml contains info on the dataset
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f"No manifest.toml file found in '{path}'.")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = tomlkit.load(f)
    except tomlkit.exceptions.TOMLKitError as e:
        raise ValueError(f"Error parsing manifest.toml: {str(e)}")

    edl_type = manifest.get("type")  # get the type
    if edl_type == "dataset":
        return "EDLDataset"
    elif edl_type == "group":
        return "EDLGroup"
    elif edl_type == "collection":
        return "EDLCollection"
    elif edl_type:  # Generic EDLUnit
        return "EDLUnit"
    else:
        raise ValueError(f"Unknown or invalid EDL type in manifest: {edl_type}")


def tsync_to_np(tsync_path: str) -> np.ndarray:
    """
    Read a .tsync file, convert to milliseconds, and convert it to a numpy array

    Args:
    tsync_path (str): Path to the input .tsync file

    Returns:
    timestamps (numpy.array): Numpy array containing all of the timestamps
    """
    # Determine if it's a legacy file or not
    if LegacyTSyncFile.is_legacy(tsync_path):
        tsync = LegacyTSyncFile(tsync_path)
    else:
        tsync = TSyncFile(tsync_path)

    tstamps = []
    for time_pair in tsync.times:
        tstamps.append(
            float(time_pair[1] / 1000)
        )  # append to list AND ensure its a float AND convert to milliseconds instead of microseconds
    timestamps = np.array(tstamps)  # convert to numpy array
    if (
        check_timestamp_error_percentage(timestamps) >= 0.05
    ):  # raise flag if more than 5% of frames are dropped
        print("Warning: More than 5% of your video's frames are dropped.")
    return timestamps


def check_timestamp_error_percentage(
    timestamps: np.ndarray, fps: int = 30, scaling_factor: float = 1000
) -> float:
    """
    Return the proportion of dropped frames relative to the respective recorded timestamps and frames per second.
    Args:
    timestamps (numpy.array): Session's recorded timestamp array.
    fps (int): Frames per second
    scaling_factor (float): factor to divide timestamps by to convert timestamp milliseconds into seconds.
    Returns:
    percentError (float): Percentage of frames that were dropped/missed during acquisition.
    """
    # https://www.mathworks.com/help/imaq/examples/determining-the-rate-of-acquisition.html
    # Find the time difference between frames.
    diff = np.diff(timestamps)
    # Check if the timestamps are in milliseconds based on the mean difference amount
    if np.mean(diff) > 10:
        # rescale the timestamps to seconds
        diff /= scaling_factor
    # Find the average time difference between frames.
    avgTime = np.mean(diff)
    # Determine the experimental frame rate.
    expRate = 1 / avgTime
    # Determine the percent error between the determined and actual frame rate.
    diffRates = abs(fps - expRate)
    percentError = diffRates / fps
    return percentError


def format(path: str) -> None:
    """
    Args:

    path (str): Path to the dataset (must be an EDLCollection). Ensure that your folder has a manifest.toml file in it AND that the manifest file says its an EDLCollection

    Returns:
    None (this function will just create a directory)
    """
    assert (
        _detect_edl_type(path) == "EDLCollection"
    ), f"Error: Expected 'EDLCollection', but got '{_detect_edl_type(path)}'"  # make sure we have an EDLCollection
    files = os.listdir(path)

    # Find metadata
    metadata_path = os.path.join(path, "orbbec-femto-camera", "metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError("There is no metadata file here")

    # Find the video
    video_src_path = os.path.join(path, "videos", "orbbec-femto-camera")
    videofile = None
    for file in os.listdir(video_src_path):
        if file.endswith(".avi") or file.endswith(".mkv") or file.endswith(".mp4"):
            videofile = os.path.join(video_src_path, file)
            break

    if not videofile:
        raise FileNotFoundError("No video file found (.avi, .mkv, .mp4)")

    for file in os.listdir(video_src_path):
        if file.endswith(".tsync"):  # convert to numpy array
            timestamps = tsync_to_np(os.path.join(video_src_path, file))
            break

    if len(timestamps) == 0:
        raise ValueError(
          "There is an error with your tsync file, please check it out."
        ) # raise Value Error if the tsync file is invalid

    # read metadata file and create directory
    with open(metadata_path, "r") as f:
        data = json.load(f)
        dataset_name = (
            f"{data['SubjectName']}_{data['SessionName']}_{data['StartTime']}"
        )

    moseq_dir = os.path.join(path, dataset_name)
    os.makedirs(moseq_dir, exist_ok=True)

    # write the video to the directory
    video_dst_path = os.path.join(moseq_dir, "depth.avi")
    shutil.copy(videofile, video_dst_path)

    # write the metadata to the directory
    metadata_dst_path = os.path.join(moseq_dir, "metadata.json")
    shutil.copy(metadata_path, metadata_dst_path)

    # write timestamps
    with open(os.path.join(moseq_dir, "depth_ts.txt"), "w") as f:
        for timestamp in timestamps:
            f.write(f"{float(timestamp)}\n")

    print(f"MoSeq directory created at {moseq_dir}")
    print(f"Video copied to {video_dst_path}")
    print(f"Timestamps file copied to {os.path.join(moseq_dir, 'depth_ts.txt')}")
    print(f"Metadata copied to {metadata_dst_path}")
