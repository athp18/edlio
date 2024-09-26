import os
import json
import shutil
import numpy as np
import tomlkit
from .dataio.tsyncfile import TSyncFile, LegacyTSyncFile


def _detect_edl_type(path: str) -> str:
    """
    Detects the type of Experimental Data Layer (EDL) unit based on the contents of the manifest.toml file.

    Args:
    path (str): Path to the dataset

    Returns:
    str: A string indicating the type of EDL unit

    Raises:
    FileNotFoundError: If the path is not a directory or if no manifest.toml file is found
    ValueError: If there's an error parsing the manifest.toml file or if the EDL type is unknown or invalid
    """
    if not os.path.isdir(path):
        raise FileNotFoundError(f"The path '{path}' is not a directory.")

    manifest_path = os.path.join(path, "manifest.toml")
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f"No manifest.toml file found in '{path}'.")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = tomlkit.load(f)
    except tomlkit.exceptions.TOMLKitError as e:
        raise ValueError(f"Error parsing manifest.toml: {str(e)}")

    edl_type = manifest.get("type")
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
    Reads a .tsync file, converts timestamps to milliseconds, and returns them as a numpy array.

    Args:
    tsync_path (str): Path to the input .tsync file

    Returns:
    numpy.ndarray: Array containing all the timestamps in milliseconds
    """
    if LegacyTSyncFile.is_legacy(tsync_path):
        tsync = LegacyTSyncFile(tsync_path)
    else:
        tsync = TSyncFile(tsync_path)

    tstamps = [float(time_pair[1] / 1000) for time_pair in tsync.times]
    timestamps = np.array(tstamps)

    if check_timestamp_error_percentage(timestamps) >= 0.05:
        print("Warning: More than 5% of your video's frames are dropped.")

    return timestamps


def check_timestamp_error_percentage(
    timestamps: np.ndarray, fps: int = 30, scaling_factor: float = 1000
) -> float:
    """
    Calculates the percentage of dropped frames in a video based on timestamp data.

    Args:
    timestamps (numpy.ndarray): Session's recorded timestamp array
    fps (int): Frames per second (default: 30)
    scaling_factor (float): Factor to convert timestamp milliseconds into seconds (default: 1000)

    Returns:
    float: Percentage of frames that were dropped/missed during acquisition
    """
    diff = np.diff(timestamps)
    if np.mean(diff) > 10:
        diff /= scaling_factor

    avg_time = np.mean(diff)
    exp_rate = 1 / avg_time
    diff_rates = abs(fps - exp_rate)
    percent_error = diff_rates / fps

    return percent_error


def format(path: str) -> None:
    """
    Converts Syntalos EDL-style data to MoSeq format.

    Args:
    path (str): Path to the EDLCollection dataset

    Raises:
    AssertionError: If the input is not an EDLCollection
    FileNotFoundError: If the metadata file is missing
    ValueError: If no video file is found or if there's an error with the .tsync file
    """
    assert (
        _detect_edl_type(path) == "EDLCollection"
    ), f"Error: Expected 'EDLCollection', but got '{_detect_edl_type(path)}'"

    # Find metadata
    metadata_path = os.path.join(path, "orbbec-femto-camera", "metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError("There is no metadata file here")

    # Find the video
    video_src_path = os.path.join(path, "videos", "orbbec-femto-camera")
    videofile = next(
        (
            os.path.join(video_src_path, file)
            for file in os.listdir(video_src_path)
            if file.endswith((".avi", ".mkv", ".mp4"))
        ),
        None,
    )

    if not videofile:
        raise ValueError("No video file found (.avi, .mkv, .mp4)")

    # Find and process the .tsync file
    tsync_file = next(
        (file for file in os.listdir(video_src_path) if file.endswith(".tsync")), None
    )
    if not tsync_file:
        raise ValueError("No .tsync file found")

    timestamps = tsync_to_np(os.path.join(video_src_path, tsync_file))

    if len(timestamps) == 0:
        raise ValueError("There is an error with your tsync file, please check it out.")

    # Read metadata and create directory
    with open(metadata_path, "r") as f:
        data = json.load(f)
        dataset_name = (
            f"{data['SubjectName']}_{data['SessionName']}_{data['StartTime']}"
        )

    moseq_dir = os.path.join(path, dataset_name)
    os.makedirs(moseq_dir, exist_ok=True)

    # Copy video
    video_dst_path = os.path.join(moseq_dir, "depth.avi")
    shutil.copy(videofile, video_dst_path)

    # Copy metadata
    metadata_dst_path = os.path.join(moseq_dir, "metadata.json")
    shutil.copy(metadata_path, metadata_dst_path)

    # Write timestamps
    with open(os.path.join(moseq_dir, "depth_ts.txt"), "w") as f:
        for timestamp in timestamps:
            f.write(f"{float(timestamp)}\n")

    print(f"MoSeq directory created at {moseq_dir}")
    print(f"Video copied to {video_dst_path}")
    print(f"Timestamps file copied to {os.path.join(moseq_dir, 'depth_ts.txt')}")
    print(f"Metadata copied to {metadata_dst_path}")
