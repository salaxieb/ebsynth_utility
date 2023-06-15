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


def ebsynth_utility_stage0_5(dbg, project_dir, original_movie_path):

    dbg.print("changing video frame rate")
    dbg.print("")

    project_dir, original_movie_path = Path(project_dir), Path(original_movie_path)

    destination = project_dir / original_movie_path.name
    if destination.exists():
        destination.unlink()

    subprocess.call(f"ffmpeg -i {str(original_movie_path)} -filter:v fps=24 {str(project_dir / original_movie_path.name)}", shell=True)

    dbg.print(f"new_file_name: {str(project_dir / original_movie_path.name)}")
    dbg.print("completed.")

