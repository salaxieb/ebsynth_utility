import subprocess

from pathlib import Path
from natsort import natsorted
from typing import List
from tqdm.contrib import tzip
from tqdm import tqdm
from PIL import Image
import shutil
import numpy as np


def hash_frame_name(frame, key_frame):
    return f"{int(frame.stem)}_{int(key_frame.stem)}_styled{frame.suffix}"


def unhash_frame_name(frame_name: Path):
    frame_name = str(frame_name.name)
    frame_nb = int(frame_name.split("_")[0])
    key_frame_nb = int(frame_name.splie("_")[1])
    return frame_nb, key_frame_nb


def frame_index(target_frame, frames_path, all_frames):
    return all_frames.index(frames_path / target_frame.name)


def run_ebsynth_for_frames(
    start: Path,
    end: Path,
    all_frames: List[Path],
    style_frame: Path,
    frames_path: Path,
    masks_path: Path,
    out_dir: Path,
):
    # start_frame = natsorted(sequence.glob("*.png"))[0]
    # end_frame = natsorted(sequence.glob("*.png"))[-1]

    # print("start_frame", start_frame, "end_frame", end_frame)
    # print(key_frame)

    # out_dir = out_dir / f'out_{start}_{end}'
    # out_dir.mkdir(exist_ok=True)

    for frame in tqdm(all_frames[frame_index(start, frames_path, all_frames): frame_index(end, frames_path, all_frames)]):
        output_path = out_dir / hash_frame_name(frame, style_frame)

        print(f"frames: {int(frame.stem)} -> {int(end.stem) + 1}")
        mask_image = Image.open(str(masks_path / frame.name))
        # empty mask
        if np.max(mask_image) == 0:
            # just copy image
            shutil.copy((frames_path / frame.name), (out_dir / frame.name))

        subprocess.run(
            [
                "/home/ubuntu/ebsynth/bin/ebsynth",
                # str(Path("C:") / "Users" / "ILDAR" / "Downloads" / "EbSynth-Beta-Win" / "EbSynth"),
                "-style",
                str(style_frame),
                "-guide",
                str(masks_path / style_frame.name),
                str(masks_path / frame.name),
                "-weight",
                "1",
                "-guide",
                str(frame.parent / style_frame.name),
                str((frame.parent / frame.name)),
                "-weight",
                "4",
                "-output",
                str(output_path),
                "-backend",
                "cuda",
            ]
        )


def ebsynth_utility_stage6(
    dbg,
    project_dir,
    frames_path,
    style_frames_path,
    masks_path,
):
    print("stage 6 begin")
    dbg.print("stage6")
    dbg.print("")

    # all_frames = [frame.stem for frame in all_frames]
    all_frames = natsorted(frames_path.glob("*.png"))

    key_style_frames = natsorted(list(style_frames_path.glob("seq_*")))
    # org_key_path = project_dir / "video_key"
    # sequences = natsorted(org_key_path.glob("seq_*"))
    out_dir = project_dir / f"out"
    out_dir.mkdir(exist_ok=True)

    for style_sequence in tqdm(key_style_frames):
        sequence_key_frames = natsorted(style_sequence.glob("*.png"))
        for i, frame in enumerate(sequence_key_frames):
            # pick up correct start and end frames for this key style frame in sequence
            # start - mid1 - mid2 - end => start - mid1, start - mid2, mid1 - end, mid2 - end
            start = sequence_key_frames[i - 1]
            if i == 0:
                start = frame
            end = sequence_key_frames[i]
            if i < len(sequence_key_frames) - 1:
                end = sequence_key_frames[i + 1]

            print(start, frame, end)

            run_ebsynth_for_frames(
                start=start,
                end=end,
                all_frames=all_frames,
                style_frame=frame,
                frames_path=frames_path,
                masks_path=masks_path,
                out_dir=out_dir,
            )

    dbg.print("")
    dbg.print("completed.")
