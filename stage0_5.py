import os
import re
import subprocess
import glob
import shutil
import time
import cv2
import numpy as np
from pathlib import Path
import shutil


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
    path = os.path.join(dir , '*.png')
    path = os.path.join(dir , '%0' + str(number_of_digits) + 'd.png')
    
    # ffmpeg -r 10 -start_number n -i snapshot_%03d.png -vframes 50 example.gif
    subprocess.call("ffmpeg -framerate " + str(fps) + " -r " + str(fps) +
                        " -start_number " + str(start) +
                        " -i " + str(path) + 
                        " -vframes " + str( vframes ) +
                        get_export_str(export_type) +
                        str(output_path), shell=True)


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
        subprocess.call(["ffmpeg", "-i", str(original_movie_path),"-vn", "-acodec", "copy", str(sound_path)], shell=True)
        
        if os.path.isfile(sound_path):
            # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4

            subprocess.call(["ffmpeg", "-i", str(no_snd_movie_path), "-i", str(sound_path), "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", str(output_path)], shell=True)
            return True
    return False

def ebsynth_utility_stage0_5(dbg, project_args, export_type):

    dbg.print("changing video frame rate")
    dbg.print("")

    project_dir, original_movie_path, *args = project_args
    project_dir, original_movie_path = Path(project_dir), Path(original_movie_path)

    destination = project_dir / original_movie_path.name
    if destination.exists():
        destination.unlink()

    subprocess.call(f"ffmpeg -i {str(original_movie_path)} -filter:v fps=12 {str(project_dir / original_movie_path.name)}", shell=True)

    dbg.print(f"new_file_name: {str(project_dir / original_movie_path.name)}")
    dbg.print("completed.")

