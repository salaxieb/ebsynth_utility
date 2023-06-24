import cv2
import shutil
import numpy as np
import math
from pathlib import Path


def get_jpg_size(filename):
    img = cv2.imread(str(filename))
    jpg_filename = Path(filename).with_suffix('.jpg')
    cv2.imwrite(str(jpg_filename), img)
    size = jpg_filename.stat().st_size
    jpg_filename.unlink()
    return size


def analyze_key_frames(
    png_dir, mask_dir, th, min_gap, max_gap, add_last_frame, is_invert_mask
):
    # correct = [(1, 33), (34, 69), (70, 76), (77, 101), (102, 111), (112, 118), (119, 125)]
    keys = []

    frames = sorted(png_dir.glob("[0-9]*.png"))

    threshold = 0.85
    mask_threshold = 0.8
    prev_img_size = get_jpg_size(frames[0])
    prev_mask_size = get_jpg_size(mask_dir / frames[0].name)
    seq_start = frames[0].stem

    for i, frame in enumerate(frames[1:], 1):
        im_size = get_jpg_size(frame)
        mask_size = get_jpg_size(mask_dir / frame.name)
        print(frame, min(prev_mask_size, mask_size) / max(prev_mask_size, mask_size))

        if any((
            min(prev_img_size, im_size) / max(prev_img_size, im_size) < threshold,
            min(prev_mask_size, mask_size) / max(prev_mask_size, mask_size) < mask_threshold
        )):
            # this frame begins new sequence
            keys.append((seq_start, frames[i-1].stem))
            print('seq_start', int(seq_start), 'seq_end', int(frames[i-1].stem))
            seq_start = frame.stem
        prev_img_size = im_size
        prev_mask_size = mask_size

    keys.append((seq_start, frames[-1].stem))

    return keys


def remove_pngs_in_dir(path):
    if not path.is_dir():
        return

    pngs = path.glob("*.png")
    for png in pngs:
        png.unlink()


def ebsynth_utility_stage2(
    dbg,
    original_movie_path,
    frame_path,
    frame_mask_path,
    org_key_path,
    key_min_gap,
    key_max_gap,
    key_th,
    key_add_last_frame,
    is_invert_mask,
):
    dbg.print("stage2")
    dbg.print("")

    original_movie_path, frame_path, frame_mask_path, org_key_path = Path(original_movie_path), Path(frame_path), Path(frame_mask_path), Path(org_key_path)

    for folder in org_key_path.glob("seq_*"):
        folder.unlink()

    remove_pngs_in_dir(org_key_path)

    dbg.print(f"fps: {fps}")
    dbg.print(f"key_min_gap: {key_min_gap}")
    dbg.print(f"key_max_gap: {key_max_gap}")
    dbg.print(f"key_th: {key_th}")

    keys = analyze_key_frames(
        frame_path,
        frame_mask_path,
        key_th,
        key_min_gap,
        key_max_gap,
        key_add_last_frame,
        is_invert_mask,
    )

    dbg.print("keys : " + str(keys))

    for i, (start, end) in enumerate(keys):
        save_path = org_key_path / f"seq_{start}_{end}"
        save_path.mkdir(exist_ok=True, parents=True)
        filename = str(start).zfill(5) + ".png"
        shutil.copy(frame_path / filename, save_path / filename)

        mid = (start + end) // 2
        filename = str(mid).zfill(5) + ".png"
        shutil.copy(frame_path / filename, save_path / filename)

        filename = str(end).zfill(5) + ".png"
        shutil.copy(frame_path / filename, save_path / filename)

    dbg.print("")
    dbg.print("Keyframes are output to [" + str(org_key_path) + "]")
    dbg.print("")
    dbg.print(
        "[Ebsynth Utility]->[configuration]->[stage 2]->[Threshold of delta frame edge]"
    )
    dbg.print(
        "The smaller this value, the narrower the keyframe spacing, and if set to 0, the keyframes will be equally spaced at the value of [Minimum keyframe gap]."
    )
    dbg.print("")
    dbg.print("If you do not like the selection, you can modify it manually.")
    dbg.print("(Delete keyframe, or Add keyframe from [" + str(frame_path) + "])")

    dbg.print("")
    dbg.print("completed.")
