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

# def search_out_dirs(proj_dir, blend_rate):
#     ### create out_dirs
#     p = re.compile(r'.*[\\\/]out\-([0-9]+)[\\\/]')

#     number_of_digits = -1
    
#     out_dirs=[]
#     for d in glob.glob( os.path.join(proj_dir ,"out-*/"), recursive=False):
#         m = p.fullmatch(d)
#         if m:
#             if number_of_digits == -1:
#                 number_of_digits = len(m.group(1))
#             out_dirs.append({ 'keyframe':int(m.group(1)), 'path':d })
    
#     out_dirs = sorted(out_dirs, key=lambda x: x['keyframe'], reverse=True)
    
#     print(number_of_digits)
    
#     prev_key = -1
#     for out_d in out_dirs:
#         out_d['next_keyframe'] = prev_key
#         prev_key = out_d['keyframe']
    
#     out_dirs = sorted(out_dirs, key=lambda x: x['keyframe'])
    
    
#     ### search start/end frame
#     prev_key = 0
#     for out_d in out_dirs:
#         imgs = sorted(glob.glob(  os.path.join( out_d['path'], '[0-9]'*number_of_digits + '.png') ))
        
#         first_img = imgs[0]
#         print(first_img)
#         basename_without_ext = os.path.splitext(os.path.basename(first_img))[0]
#         blend_timing = (prev_key - out_d['keyframe'])*blend_rate + out_d['keyframe']
#         blend_timing = round(blend_timing)
#         start_frame = max( blend_timing, int(basename_without_ext) )
#         out_d['startframe'] = start_frame
        
#         last_img = imgs[-1]
#         print(last_img)
#         basename_without_ext = os.path.splitext(os.path.basename(last_img))[0]
#         end_frame = min( out_d['next_keyframe'], int(basename_without_ext) )
#         if end_frame == -1:
#             end_frame = int(basename_without_ext)
#         out_d['endframe'] = end_frame
#         prev_key = out_d['keyframe']
    
#     return number_of_digits, out_dirs

def get_ext(export_type):
    if export_type in ("mp4","webm","gif"):
        return "." + export_type
    else:
        return ".avi"

def trying_to_add_audio(original_movie_path, no_snd_movie_path, output_path, tmp_dir ):
    if os.path.isfile(original_movie_path):
        sound_path = os.path.join(tmp_dir , 'sound.mp4')
        subprocess.call("ffmpeg -i " + original_movie_path + " -vn -acodec copy " + sound_path, shell=True)
        
        if os.path.isfile(sound_path):
            # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4

            subprocess.call("ffmpeg -i " + no_snd_movie_path + " -i " + sound_path + " -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 " + output_path, shell=True)
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
    blend_rate = clamp(blend_rate, 0.0, 1.0)
    dbg.print("blend_rate: {}".format(blend_rate))

    # project_dir = Path(project_dir)
    
    # tmp_dir = project_dir / "crossfade_tmp"

    # if tmp_dir.is_dir():
    #     shutil.rmtree(tmp_dir)
    # tmp_dir.mkdir()
    
    # out_dir_name = project_dir / 'out'

    # black_img = np.zeros_like(
    #     cv2.imread(
    #         os.path.join(
    #             out_dirs[cur_clip]['path'],
    #             str(start).zfill(number_of_digits) + ".png"
    #     )))

    # for image in out_dir_name.glob('*.png'):
    #     shutil.copy(image, tmp_dir)
    
    
    dbg.print("")
    dbg.print("completed.")

