import cv2
import os
import glob
import shutil
import numpy as np
from PIL import Image

from color_matcher import ColorMatcher
from color_matcher.normalizer import Normalizer


def resize_img(img, w, h):
    if img.shape[0] + img.shape[1] < h + w:
        interpolation = interpolation = cv2.INTER_CUBIC
    else:
        interpolation = interpolation = cv2.INTER_AREA

    return cv2.resize(img, (w, h), interpolation=interpolation)


def get_pair_of_img(img_path, target_dir):
    target_path = target_dir / img_path.name
    return target_path if target_path.is_file() else None


def remove_pngs_in_dir(path):
    if not path.is_dir():
        return

    for png in path.glob("*.png"):
        png.unlink()


def get_pair_of_img(img, target_dir):
    pair_path = target_dir / img.name
    if pair_path.is_file():
        return pair_path
    print(f"!!! pair of {img} not in {target_dir}")
    return ""


def get_mask_array(mask_path):
    if not mask_path:
        return None
    mask_array = np.asarray(Image.open(mask_path))
    if mask_array.ndim == 2:
        mask_array = mask_array[:, :, np.newaxis]
    mask_array = mask_array[:, :, :1]
    mask_array = mask_array / 255
    return mask_array


def color_match(imgs, ref_image, color_matcher_method, dst_path):
    cm = ColorMatcher(method=color_matcher_method)

    i = 0
    total = len(imgs)

    for fname in imgs:

        img_src = Image.open(fname)
        img_src = Normalizer(np.asarray(img_src)).type_norm()

        img_src = cm.transfer(src=img_src, ref=ref_image, method=color_matcher_method)

        img_src = Normalizer(img_src).uint8_norm()
        Image.fromarray(img_src).save(str(dst_path / fname.name))

        i += 1
        print(f"{i}/{total}")

    imgs = sorted(dst_path.glob("*.png"))


def ebsynth_utility_stage3_5(
    dbg,
    project_args,
    color_matcher_method,
    st3_5_use_mask,
    st3_5_use_mask_ref,
    st3_5_use_mask_org,
    color_matcher_ref_type,
    color_matcher_ref_image,
):
    dbg.print("stage3.5")
    dbg.print("")

    (
        _,
        _,
        frame_path,
        frame_mask_path,
        org_key_path,
        img2img_key_path,
        *args,
    ) = project_args

    backup_path = img2img_key_path.parent / "st3_5_backup_img2img_key"

    if not backup_path.is_dir():
        dbg.print(f"{backup_path} not found -> create backup.")
        backup_path.mkdir(exist_ok=True)

        imgs = img2img_key_path.glob("*.png")

        for img in imgs:
            pair_path = backup_path / img.name
            shutil.copy(img, pair_path)

    else:
        dbg.print(
            "{0} found -> Treat the images here as originals.".format(backup_path)
        )

    org_imgs = sorted(backup_path.glob("*.png"))
    head_of_keyframe = org_imgs[0]

    # open ref img
    ref_image = color_matcher_ref_image
    if not ref_image:
        dbg.print("color_matcher_ref_image not set")

        if color_matcher_ref_type == 0:
            #'original video frame'
            dbg.print("select -> original video frame")
            ref_image = Image.open(get_pair_of_img(head_of_keyframe, frame_path))
        else:
            #'first frame of img2img result'
            dbg.print("select -> first frame of img2img result")
            ref_image = Image.open(get_pair_of_img(head_of_keyframe, backup_path))

        ref_image = np.asarray(ref_image)

        if st3_5_use_mask_ref:
            mask = get_pair_of_img(head_of_keyframe, frame_mask_path)
            if mask:
                mask_array = get_mask_array(mask)
                ref_image = ref_image * mask_array
                ref_image = ref_image.astype(np.uint8)

    else:
        dbg.print("select -> color_matcher_ref_image")
        ref_image = np.asarray(ref_image)

    if color_matcher_method in ("mvgd", "hm-mvgd-hm"):
        sample_img = Image.open(head_of_keyframe)
        ref_image = resize_img(ref_image, sample_img.width, sample_img.height)

    ref_image = Normalizer(ref_image).type_norm()

    if st3_5_use_mask_org:
        tmp_path = img2img_key_path.parent / "st3_5_tmp"
        dbg.print(f"create {tmp_path} for masked original image")

        remove_pngs_in_dir(tmp_path)
        tmp_path.mkdir(exist_ok=True)

        for org_img in org_imgs:
            org_image = np.asarray(Image.open(str(org_img)))

            mask = get_pair_of_img(org_img, frame_mask_path)
            if mask:
                mask_array = get_mask_array(mask)
                org_image = org_image * mask_array
                org_image = org_image.astype(np.uint8)

            Image.fromarray(org_image).save(str(tmp_path / org_img.name))

        org_imgs = sorted(tmp_path.glob("*.png"))

    color_match(org_imgs, ref_image, color_matcher_method, img2img_key_path)

    if st3_5_use_mask or st3_5_use_mask_org:
        imgs = sorted(img2img_key_path.glob("*.png"))
        for img in imgs:
            mask = get_pair_of_img(img, frame_mask_path)
            if mask:
                mask_array = get_mask_array(mask)
                bg = get_pair_of_img(img, frame_path)
                bg_image = np.asarray(Image.open(bg))
                fg_image = np.asarray(Image.open(img))

                final_img = fg_image * mask_array + bg_image * (1 - mask_array)
                final_img = final_img.astype(np.uint8)

                Image.fromarray(final_img).save(img)

    dbg.print("")
    dbg.print("completed.")
