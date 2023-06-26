# import os
# import re
# import subprocess
# import glob
# import shutil
# import time
# import cv2
# import numpy as np
# from extensions.ebsynth_utility.stage7 import clamp, search_out_dirs


# def ebsynth_utility_stage7(dbg, project_dir_front, project_dir_back, frame_mask_path, back_mask_path):
#     # pixel_front_img_1 -> 4
#     # mask_img_1 -> 0.1
#     # pixel_front_img_2 -> 10
#     # mask_img_2 -> 0.2

#     # pixel_back_img_1 -> 20
#     # mask_img_1 -> 0.9
#     # pixel_back_img_2 -> 15
#     # mask_img_2 -> 0.8

#     # now: (4 + 10) / 2 * 0.15 + (20 + 15) / 2 * 0.85
#     # must be: 4 * 0.1 + 10 * 0.2

#     dbg.print("stage6_9")
#     dbg.print("")

#     number_of_digits, out_dirs_front = search_out_dirs(project_dir_front, blend_rate)
#     number_of_digits, out_dirs_back = search_out_dirs(project_dir_back, blend_rate)


#     front_frames = Path(project_dir) / "crossfade_tmp"
#     back_frames = Path(back_path) / "crossfade_tmp"
#     frame_mask_path = Path(frame_mask_path)
#     back_mask_path = Path(back_mask_path)

#     mixed_out_path = Path(project_dir_front) / "front_back_crossfade_tmp"
#     mixed_out_path.mkdir(exist_ok=True)

#     for out_dir_front in out_dirs_front:
#         key_frame = out_dir_front['keyframe']
#         # if image bdefore keyfrome, join with front
#         # if image bahind frame, join with one in behind
#         for frame in range(out_dir_front['start_frame']), key_frame


#     ### create frame imgs
#     for front_image_filename in tqdm(front_frames.glob('*.png')):
#         front_image = Image.open(str(front_image_filename))
#         front_mask_image = Image.open(str(frame_mask_path / front_image_filename.name)).convert('L')

#         back_image = Image.open(str(back_frames / front_image_filename.name))
#         back_mask_image = Image.open(str(back_mask_path / front_image_filename.name)).convert('L')

#         final_image = Image.composite(front_image, back_image, front_mask_image)

#         final_image.save(str(mixed_crossfade_path / front_image_filename.name))
