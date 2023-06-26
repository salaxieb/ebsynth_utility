import cv2
import re
import os
import glob
import time

from sys import byteorder
import binascii
from pathlib import Path
import numpy as np

SYNTHS_PER_PROJECT = 15


def to_float_bytes(f):
    if byteorder == "little":
        return np.array([float(f)], dtype="<f4").tobytes()
    else:
        return np.array([float(f)], dtype=">f4").tobytes()


def path2framenum(path):
    return int(path.stem)


def search_key_dir(key_dir):
    frames = sorted(key_dir.glob("[0-9]*.png"))

    basename = frames[0].stem

    key_list = [path2framenum(key) for key in frames]

    print("digits = " + str(len(basename)))
    print("keys = " + str(key_list))

    return len(basename), key_list


def search_video_dir(video_dir):
    frames = sorted(video_dir.glob("[0-9]*.png"))

    first = path2framenum(frames[0])
    last = path2framenum(frames[-1])

    return first, last


def export_project(project, proj_filename):

    proj_path = (Path(project["proj_dir"]) / proj_filename).with_suffix(".ebs")

    with open(proj_path, "wb") as f:
        # header
        f.write(binascii.unhexlify("45"))
        f.write(binascii.unhexlify("42"))
        f.write(binascii.unhexlify("53"))
        f.write(binascii.unhexlify("30"))
        f.write(binascii.unhexlify("35"))
        f.write(binascii.unhexlify("00"))

        # video
        f.write(len(project["video_dir"] + project["file_name"]).to_bytes(4, byteorder))
        f.write((project["video_dir"] + project["file_name"]).encode())

        # mask
        if project["mask_dir"]:
            f.write(
                len(project["mask_dir"] + project["file_name"]).to_bytes(4, byteorder)
            )
            f.write((project["mask_dir"] + project["file_name"]).encode())
        else:
            f.write(int(0).to_bytes(4, byteorder))

        # key
        f.write(len(project["key_dir"] + project["file_name"]).to_bytes(4, byteorder))
        f.write((project["key_dir"] + project["file_name"]).encode())

        # mask on flag
        if project["mask_dir"]:
            f.write(int(1).to_bytes(1, byteorder))
        else:
            f.write(int(0).to_bytes(1, byteorder))

        # keyframe weight
        f.write(to_float_bytes(project["key_weight"]))

        # video weight
        f.write(to_float_bytes(project["video_weight"]))

        # mask weight
        f.write(to_float_bytes(project["mask_weight"]))

        # mapping
        f.write(to_float_bytes(project["adv_mapping"]))

        # de-flicker
        f.write(to_float_bytes(project["adv_de-flicker"]))

        # diversity
        f.write(to_float_bytes(project["adv_diversity"]))

        # num of synths
        f.write(len(project["synth_list"]).to_bytes(4, byteorder))

        # synth
        for synth in project["synth_list"]:
            # key frame
            f.write(int(synth["key"]).to_bytes(4, byteorder))
            # is start frame exist
            f.write(int(1).to_bytes(1, byteorder))
            # is end frame exist
            f.write(int(1).to_bytes(1, byteorder))
            # start frame
            f.write(int(synth["prev_key"]).to_bytes(4, byteorder))
            # end frame
            f.write(int(synth["next_key"]).to_bytes(4, byteorder))

            # out path
            path = (
                "out-"
                + str(synth["key"]).zfill(project["number_of_digits"])
                + project["file_name"]
            )
            f.write(len(path).to_bytes(4, byteorder))
            f.write(path.encode())

        # ?
        f.write(binascii.unhexlify("56"))
        f.write(binascii.unhexlify("30"))
        f.write(binascii.unhexlify("32"))
        f.write(binascii.unhexlify("00"))

        # synthesis detail
        f.write(int(project["adv_detail"]).to_bytes(1, byteorder))

        # padding
        f.write(binascii.unhexlify("00"))
        f.write(binascii.unhexlify("00"))
        f.write(binascii.unhexlify("00"))

        # use gpu
        f.write(int(project["adv_gpu"]).to_bytes(1, byteorder))

        # ?
        f.write(binascii.unhexlify("00"))
        f.write(binascii.unhexlify("00"))
        f.write(binascii.unhexlify("F0"))
        f.write(binascii.unhexlify("41"))
        f.write(binascii.unhexlify("C0"))
        f.write(binascii.unhexlify("02"))
        f.write(binascii.unhexlify("00"))
        f.write(binascii.unhexlify("00"))


def rename_keys(key_dir):
    imgs = key_dir.glob("*.png")

    if not imgs:
        print("no files in %s" % key_dir)
        return

    p = re.compile(r"([0-9]+).*\.png")

    for img in imgs:
        m = p.fullmatch(img.name)

        if m:
            f = m.group(1) + ".png"
            dirname = img.parent.name
            img.rename(Path(dirname) / f)


def ebsynth_utility_stage5(
    dbg,
    project_dir,
    frame_path,
    frame_mask_path,
    img2img_key_path,
    img2img_upscale_key_path,
):
    dbg.print("stage5")
    dbg.print("")

    if not project_dir.is_dir():
        dbg.print("project_dir : no such dir %s" % project_dir)
        return
    if not frame_path.is_dir():
        dbg.print("frame_path : no such dir %s" % frame_path)
        return

    no_upscale = False

    if not img2img_upscale_key_path.is_dir():
        dbg.print(
            "img2img_upscale_key_path : no such dir %s" % img2img_upscale_key_path
        )
        if not img2img_key_path.is_dir():
            return

        sample_img2img_key = list(img2img_key_path.glob("*.png"))[0]
        img_height1, img_width1, _ = cv2.imread(str(sample_img2img_key)).shape
        sample_frame = list(frame_path.glob("*.png"))[0]
        img_height2, img_width2, _ = cv2.imread(str(sample_frame)).shape

        if img_height1 != img_height2 or img_width1 != img_width2:
            return

        dbg.print(
            "The size of frame and img2img_key matched. use %s instead"
            % img2img_key_path
        )
        img2img_upscale_key_path = img2img_key_path
        no_upscale = True

    else:
        rename_keys(img2img_upscale_key_path)

    number_of_digits, keys = search_key_dir(img2img_upscale_key_path)

    if number_of_digits == -1:
        dbg.print("no key frame")
        return

    first_frame, last_frame = search_video_dir(frame_path)

    ### add next key
    synth_list = []
    next_key = last_frame

    for key in keys[::-1]:
        synth_list.append({"next_key": next_key})
        next_key = key

    synth_list = synth_list[::-1]
    prev_key = first_frame

    ### add key / prev key
    for i, key in enumerate(keys):
        synth_list[i]["key"] = key
        synth_list[i]["prev_key"] = prev_key
        prev_key = key

    try:
        relative_video_dir = str(Path(frame_path).relative_to(Path(project_dir)))
    except ValueError:
        # it means that relative path thru parent
        relative_video_dir = "../" + Path(frame_path).stem
    relative_mask_dir = str(Path(frame_mask_path).relative_to(Path(project_dir)))

    project = {
        "proj_dir": project_dir,
        "file_name": "/[" + "#" * number_of_digits + "].png",
        "number_of_digits": number_of_digits,
        "key_dir": "img2img_upscale_key" if no_upscale == False else "img2img_key",
        "video_dir": relative_video_dir,
        "mask_dir": relative_mask_dir,
        "key_weight": 1.0,
        "video_weight": 4.0,
        "mask_weight": 1.0,
        "adv_mapping": 10.0,
        "adv_de-flicker": 1.0,
        "adv_diversity": 3500.0,
        "adv_detail": 1,  # high
        "adv_gpu": 1,  # use gpu
    }

    if not frame_mask_path:
        # no mask
        project["mask_dir"] = ""

    proj_base_name = time.strftime("%Y%m%d-%H%M%S")
    # if is_invert_mask:
    # proj_base_name = "inv_" + proj_base_name

    tmp = []
    proj_index = 0
    for i, synth in enumerate(synth_list):
        tmp.append(synth)
        if i % SYNTHS_PER_PROJECT == SYNTHS_PER_PROJECT - 1:
            project["synth_list"] = tmp
            proj_file_name = proj_base_name + "_" + str(proj_index).zfill(5)
            export_project(project, proj_file_name)
            proj_index += 1
            tmp = []
            dbg.print("exported : " + proj_file_name + ".ebs")

    if tmp:
        project["synth_list"] = tmp
        proj_file_name = proj_base_name + "_" + str(proj_index).zfill(5)
        export_project(project, proj_file_name)
        proj_index += 1
        dbg.print("exported : " + proj_file_name + ".ebs")

    dbg.print("")
    dbg.print("completed.")
