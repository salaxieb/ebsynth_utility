import subprocess

from pathlib import Path
from natsort import natsorted
from tqdm import tqdm
import shutil


def ebsynth_utility_stage6(dbg, project_dir, frames_path, style_frames_path, masks_path):
    dbg.print("stage6")
    dbg.print("")

    project_dir = Path(project_dir)
    frames_path = Path(frames_path)
    style = Path(style_frames_path)
    masks_path = Path(masks_path)

    all_frames = natsorted(list(frames_path.glob('*.png')))
    all_frames = [frame.stem for frame in all_frames]

    key_style_frames = natsorted(list(style.glob('*.png')))

    for i, key_frame in enumerate(tqdm(key_style_frames)):
        out_dir_name = project_dir / f'out-{key_frame.stem}'
        out_dir_name.mkdir(exist_ok=True)
        # style frames before
        frame = "00000"
        if i > 0:
            for frame in all_frames[all_frames.index(key_style_frames[i-1].stem): all_frames.index(key_style_frames[i].stem) +  1]:
                mask_image = Image.open(str(masks_path / frame.name))
                # empty mask
                print('max mask', np.max(mask_image))
                if np.max(mask_image) == 0:
                    # just copy image
                    shutil.copy((frames_path / frame).with_suffix(".png"), (out_dir_name / frame).with_suffix(".png"))

                subprocess.run([
                    "/home/ubuntu/ebsynth/bin/ebsynth",
                    # str(Path("C:") / "Users" / "ILDAR" / "Downloads" / "EbSynth-Beta-Win" / "EbSynth"),
                    "-style", str(key_frame),
                    "-guide", str(masks_path / key_frame.name), str(masks_path / frame.name),
                    "-weight", "1",
                    "-guide", str(frames_path / key_frame.name), str((frames_path / frame).with_suffix(".png")),
                    "-weight", "4",
                    "-output", str((out_dir_name / frame).with_suffix(".png")),
                    "-backend", 'cuda',
                ])
        # style frames after
        if i < len(key_style_frames) - 1:
            for frame in all_frames[all_frames.index(key_style_frames[i].stem): all_frames.index(key_style_frames[i+1].stem) + 1]:
                mask_image = Image.open(str(masks_path / frame.name))
                # empty mask
                print('max mask', np.max(mask_image))
                if np.max(mask_image) == 0:
                    # just copy image
                    shutil.copy((frames_path / frame).with_suffix(".png"), (out_dir_name / frame).with_suffix(".png"))
                subprocess.run([
                    "/home/ubuntu/ebsynth/bin/ebsynth",
                    # str(Path("C:") / "Users" / "ILDAR" / "Downloads" / "EbSynth-Beta-Win" / "EbSynth"),
                    "-style", str(key_frame),
                    "-guide", str(masks_path / key_frame.name), str(masks_path / frame.name),
                    "-weight", "1",
                    "-guide", str(frames_path / key_frame.name), str((frames_path / frame).with_suffix(".png")),
                    "-weight", "4",
                    "-output", str((out_dir_name / frame).with_suffix(".png")),
                    "-backend", 'cuda',
                ])

    dbg.print("")
    dbg.print("completed.")

