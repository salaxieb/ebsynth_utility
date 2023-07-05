import os
import re
import subprocess
import glob
import shutil
import time
import cv2
import numpy as np
from pathlib import Path
import shutil


def ebsynth_utility_stage0_5(dbg, project_dir, original_movie_path, target_fps):

    dbg.print("changing video frame rate")
    dbg.print("")

    if not project_dir.is_dir():
        project_dir.mkdir(exist_ok=True)

    destination = project_dir / original_movie_path.name
    if destination.exists():
        destination.unlink()

    subprocess.call(
        f"ffmpeg -i {str(original_movie_path)} -filter:v fps={target_fps} {str(destination)}",
        shell=True,
    )

    dbg.print(f"new_file_name: {str(destination)}")
    dbg.print("completed.")
    return destination
