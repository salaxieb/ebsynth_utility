import os
import re
import subprocess
import glob
import shutil
import time
import cv2
import numpy as np
from pathlib import Path


def clamp(n, smallest, largest):
    return sorted([smallest, n, largest])[1]


def remove_pngs_in_dir(path):
    if not path.is_dir():
        return
    
    pngs = path.glob("*.png")
    for png in pngs:
        png.unlink()


def create_movie_from_frames( dir, start, end, number_of_digits, fps, output_path, export_type):
    def get_export_str(export_type):
        if export_type == "mp4":
            return " -vcodec libx264 -pix_fmt yuv420p "
        elif export_type == "webm":
#            return " -vcodec vp9 -crf 10 -b:v 0 "
            return " -crf 40 -b:v 0 -threads 4 "
        elif export_type == "gif":
            return " "
        elif export_type == "rawvideo":
            return " -vcodec rawvideo -pix_fmt bgr24 "

    vframes = end - start + 1
    path = os.path.join(dir , '%0' + str(number_of_digits) + 'd.png')
    
    # ffmpeg -r 10 -start_number n -i snapshot_%03d.png -vframes 50 example.gif
    subprocess.call("ffmpeg -framerate " + str(fps) + " -r " + str(fps) +
                        " -start_number " + str(start) +
                        " -i " + path + 
                        " -vframes " + str( vframes ) +
                        get_export_str(export_type) +
                        output_path, shell=True)


def search_out_dirs(proj_dir, blend_rate):
    ### create out_dirs
    p = re.compile(r'.*[\\\/]out\-([0-9]+)[\\\/]')

    number_of_digits = -1
    
    out_dirs=[]
    for d in glob.glob( os.path.join(proj_dir ,"out-*/"), recursive=False):
        m = p.fullmatch(d)
        if m:
            if number_of_digits == -1:
                number_of_digits = len(m.group(1))
            out_dirs.append({ 'keyframe':int(m.group(1)), 'path':d })
    
    out_dirs = sorted(out_dirs, key=lambda x: x['keyframe'], reverse=True)
    
    print(number_of_digits)
    
    prev_key = -1
    for out_d in out_dirs:
        out_d['next_keyframe'] = prev_key
        prev_key = out_d['keyframe']
    
    out_dirs = sorted(out_dirs, key=lambda x: x['keyframe'])
    
    
    ### search start/end frame
    prev_key = 0
    for out_d in out_dirs:
        imgs = sorted(glob.glob(  os.path.join( out_d['path'], '[0-9]'*number_of_digits + '.png') ))
        
        first_img = imgs[0]
        print(first_img)
        basename_without_ext = os.path.splitext(os.path.basename(first_img))[0]
        blend_timing = (prev_key - out_d['keyframe'])*blend_rate + out_d['keyframe']
        blend_timing = round(blend_timing)
        start_frame = max( blend_timing, int(basename_without_ext) )
        out_d['startframe'] = start_frame
        
        last_img = imgs[-1]
        print(last_img)
        basename_without_ext = os.path.splitext(os.path.basename(last_img))[0]
        end_frame = min( out_d['next_keyframe'], int(basename_without_ext) )
        if end_frame == -1:
            end_frame = int(basename_without_ext)
        out_d['endframe'] = end_frame
        prev_key = out_d['keyframe']
    
    return number_of_digits, out_dirs

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

def ebsynth_utility_stage0_5(dbg, project_args, export_type):

    dbg.print("splitting to frames")
    dbg.print("")

    if st1_masking_method_index == 1 and (not clipseg_mask_prompt):
        dbg.print("Error: clipseg_mask_prompt is Empty")
        return

    project_dir, original_movie_path, frame_path, frame_mask_path, _, _, _ = project_args
    project_dir, original_movie_path, frame_path, frame_mask_path = Path(project_dir), Path(original_movie_path), Path(frame_path), Path(frame_mask_path)

    if is_invert_mask:
        if frame_path.is_dir() and frame_mask_path.is_dir():
            dbg.print("Skip as it appears that the frame and normal masks have already been generated.")
            return

    if os.path.isdir( frame_path ):
        dbg.print("Skip frame extraction")
    else:
        os.makedirs(frame_path, exist_ok=True)
        png_path = os.path.join(frame_path , "%05d.png")
        # ffmpeg.exe -ss 00:00:00  -y -i %1 -qscale 0 -f image2 -c:v png "%05d.png"
        subprocess.call("ffmpeg -ss 00:00:00  -y -i " + original_movie_path + " -qscale 0 -f image2 -c:v png " + png_path, shell=True)

    
    dbg.print('making video desired framerate 10 - 19 fps')

    fps = 30
    clip = cv2.VideoCapture(original_movie_path)
    if clip:
        fps = clip.get(cv2.CAP_PROP_FPS)
        clip.release()

    desired_fps = 12
    # 30 // 10 = 2, fps -> 15
    # 20 // 10 -> 1, fps -> 20
    # 60 // 10 = 5, fps -> 12
    # 45 // 10 = 3, fps -> 15
    each_n_th_frame = fps // desired_fps
    all_frames = list(Path(png_path).glob("*.png"))
    keep_frames = {all_frames[0], all_frames[-1]}

    for i in range(0, len(all_frames), each_n_th_frame):
        keep_frames.add(all_frames[i])
    
    for frame in all_frames:
        if frame not in keep_frames:
            frame.unlink()

    dbg.print("joining frames back")
    dbg.print("")

    tmp_dir = os.path.join(project_dir , "")

    nosnd_path = os.path.join(project_dir , movie_base_name + get_ext(export_type))
    
    start = int(all_frames[0].stem)
    end = int(all_frames[-1].stem)

    create_movie_from_frames(tmp_dir, start, end, number_of_digits, fps, nosnd_path, export_type)

    dbg.print("exported : " + nosnd_path)
    
    if export_type == "mp4":

        with_snd_path = os.path.join(project_dir , movie_base_name + '_with_snd.mp4')

        if trying_to_add_audio(original_movie_path, nosnd_path, with_snd_path, tmp_dir):
            dbg.print("exported : " + with_snd_path)
    
    dbg.print("")
    dbg.print("completed.")

