import os
import re
import subprocess
import glob
import shutil
import time
import cv2
import numpy as np
import itertools
from extensions.ebsynth_utility.stage7_5 import (
    create_movie_from_frames,
    get_ext,
    trying_to_add_audio,
)


def clamp(n, smallest, largest):
    return sorted([smallest, n, largest])[1]


def resize_img(img, w, h):
    if img.shape[0] + img.shape[1] < h + w:
        interpolation = interpolation = cv2.INTER_CUBIC
    else:
        interpolation = interpolation = cv2.INTER_AREA

    return cv2.resize(img, (w, h), interpolation=interpolation)


def merge_bg_src(
    base_frame_dir,
    bg_dir,
    frame_mask_path,
    tmp_dir,
    bg_type,
    mask_blur_size,
    mask_threshold,
    fg_transparency,
):

    base_frames = sorted(base_frame_dir.glob("[0-9]*.png"))

    bg_frames = sorted(bg_dir / "*.png")

    def bg_frame(total_frames):
        bg_len = len(bg_frames)

        if bg_type == "Loop":
            itr = itertools.cycle(bg_frames)
            while True:
                yield next(itr)
        else:
            for i in range(total_frames):
                yield bg_frames[int(bg_len * (i / total_frames))]

    bg_itr = bg_frame(len(base_frames))

    for base_frame in base_frames:
        im = cv2.imread(base_frame)
        bg = cv2.imread(next(bg_itr))
        bg = resize_img(bg, im.shape[1], im.shape[0])

        mask_path = frame_mask_path / base_frame.name
        mask = cv2.imread(mask_path)[:, :, 0]

        mask[mask < int(255 * mask_threshold)] = 0

        if mask_blur_size > 0:
            mask_blur_size = mask_blur_size // 2 * 2 + 1
            mask = cv2.GaussianBlur(mask, (mask_blur_size, mask_blur_size), 0)
        mask = mask[:, :, np.newaxis]

        fore_rate = (mask / 255) * (1 - fg_transparency)

        im = im * fore_rate + bg * (1 - fore_rate)
        im = im.astype(np.uint8)
        cv2.imwrite(str(tmp_dir / base_frame.name), im)


def extract_frames(movie_path, output_dir, fps):
    png_path = output_dir / "%05d.png"
    # ffmpeg.exe -ss 00:00:00  -y -i %1 -qscale 0 -f image2 -c:v png "%05d.png"
    subprocess.call(
        f"ffmpeg -ss 00:00:00  -y -i {movie_path} -vf fps={str(round(fps, 2))} -qscale 0 -f image2 -c:v png {png_path}",
        shell=True,
    )


def ebsynth_utility_stage8(
    dbg,
    project_args,
    bg_src,
    bg_type,
    mask_blur_size,
    mask_threshold,
    fg_transparency,
    export_type,
):
    dbg.print("stage8")
    dbg.print("")

    if not bg_src:
        dbg.print("Fill [configuration] -> [stage 8] -> [Background source]")
        return

    project_dir, original_movie_path, _, frame_mask_path, *args = project_args

    fps = 30
    clip = cv2.VideoCapture(original_movie_path)
    if clip:
        fps = clip.get(cv2.CAP_PROP_FPS)
        clip.release()

    dbg.print("bg_src: {}".format(bg_src))
    dbg.print("bg_type: {}".format(bg_type))
    dbg.print("mask_blur_size: {}".format(mask_blur_size))
    dbg.print("export_type: {}".format(export_type))
    dbg.print("fps: {}".format(fps))

    base_frame_dir = project_dir / "crossfade_tmp"

    if not base_frame_dir.is_dir():
        dbg.print(f"{base_frame_dir} base frame not found")
        return

    tmp_dir = project_dir / "bg_merge_tmp"
    if tmp_dir.is_dir():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(exist_ok=True)

    ### create frame imgs
    if bg_src.is_file():
        bg_ext = bg_src.suffix
        if bg_ext == ".mp4":
            bg_tmp_dir = project_dir / "bg_extract_tmp"
            if bg_tmp_dir.is_dir():
                shutil.rmtree(bg_tmp_dir)
            bg_tmp_dir.mkdir(exist_ok=True)

            extract_frames(bg_src, bg_tmp_dir, fps)

            bg_src = bg_tmp_dir
        else:
            dbg.print(f"{bg_src} must be mp4 or directory")
            return
    elif not bg_src.is_dir():
        dbg.print(f"{bg_src} must be mp4 or directory")
        return

    merge_bg_src(
        base_frame_dir,
        bg_src,
        frame_mask_path,
        tmp_dir,
        bg_type,
        mask_blur_size,
        mask_threshold,
        fg_transparency,
    )

    ### create movie
    movie_base_name = time.strftime("%Y%m%d-%H%M%S")
    movie_base_name = "merge_" + movie_base_name

    nosnd_path = (project_dir / movie_base_name).with_suffix(get_ext(export_type))

    merged_frames = sorted(tmp_dir.glob("[0-9]*.png"))
    start = int(merged_frames[0].stem)
    end = int(merged_frames[-1].stem)

    create_movie_from_frames(tmp_dir, start, end, 5, fps, nosnd_path, export_type)

    dbg.print("exported : " + nosnd_path)

    if export_type == "mp4":

        with_snd_path = project_dir / (movie_base_name + "_with_snd.mp4")

        if trying_to_add_audio(original_movie_path, nosnd_path, with_snd_path, tmp_dir):
            dbg.print("exported : " + with_snd_path)

    dbg.print("")
    dbg.print("completed.")
