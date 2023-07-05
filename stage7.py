import os
import re
import subprocess
import glob
import shutil
import time
import cv2
import numpy as np

from collections import defaultdict
from typing import Tuple

from pathlib import Path
from natsort import natsorted

from PIL import Image

from stage6 import unhash_frame_name


def clamp(n, smallest, largest):
    return sorted([smallest, n, largest])[1]


def search_out_frames(project_dir):
    styled_frames = defaultdict(list)
    for frame_path in (project_dir / "out").glob("*.png"):
        frame_nb, key_fame_nb = unhash_frame_name(frame_path)
        styled_frames[frame_nb].append((key_fame_nb, frame_path))
    return styled_frames


def weighted_sum(styles_with_weights: Tuple[float, Path]):
    assert len(styles_with_weights) == 2
    assert styles_with_weights[0][0] + styles_with_weights[1][0] == 1
    
    img_f = cv2.imread(str(styles_with_weights[0][1]))
    img_b = cv2.imread(str(styles_with_weights[1][1]))

    return cv2.addWeighted(img_f, styles_with_weights[0][0], img_b, styles_with_weights[1][0], 0)


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
    # crossfading

    crossfade_folder = project_dir / "crossfade"
    crossfade_folder.mkdir(exist_ok=True)

    styled_frames_maping = search_out_frames(project_dir)

    # style 3, style 14, frame 6
    # (6 - 3) / (14 - 3) = 3 / 11
    # 3/11 * style 3, 8/11 * style 14

    for frame, styled_frames in tqdm(styled_frames_maping.items()):
        # resulting image is weighted sum of two styled images
        save_path = (crossfade_folder / str(frame).zfill(5)).with_suffix(".png")
        styles_with_distances = [(abs(key_frame_nb - frame), styled_image_path) for key_frame_nb, styled_image_path in styled_frames]

        distances_sum = sum(distance for distance, img_path in styles_with_distances)
        styles_with_weights = [
            (distance / distances_sum, img_path) for distance, img_path in styles_with_distances
        ]

        resulting_image = weighted_sum(styles_with_weights)
        cv2.imwrite(str(save_path), resulting_image)

    dbg.print("")
    dbg.print("completed.")
