import os
import re
import subprocess
import glob
import shutil
import time
import cv2
import numpy as np
from natsort import natsorted


def clamp(n, smallest, largest):
    return sorted([smallest, n, largest])[1]


def get_ext(export_type):
    if export_type in ("mp4", "webm", "gif"):
        return "." + export_type
    else:
        return ".avi"


def trying_to_add_audio(original_movie_path, no_snd_movie_path, output_path, tmp_dir):
    if original_movie_path.is_file():
        sound_path = tmp_dir / "sound.mp4"
        subprocess.call(
            f"ffmpeg -i {original_movie_path} -vn -acodec copy {sound_path}", shell=True
        )

        if sound_path.is_file():
            # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4

            subprocess.call(
                f"ffmpeg -i {no_snd_movie_path} -i {sound_path} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 {output_path}",
                shell=True,
            )
            return True

    return False


def ebsynth_utility_stage7(dbg, project_dir, blend_rate):
    # pixel_front_img_1 -> 4
    # mask_img_1 -> 0.1
    # pixel_front_img_2 -> 10
    # mask_img_2 -> 0.2

    # pixel_back_img_1 -> 20
    # mask_img_1 -> 0.9
    # pixel_back_img_2 -> 15
    # mask_img_2 -> 0.8

    # now: (4 + 10) / 2 * 0.15 + (20 + 15) / 2 * 0.85
    # must be: 4 * 0.1 + 10 * 0.2

    dbg.print("stage7")
    dbg.print("")

    dbg.print("")
    dbg.print("completed.")
