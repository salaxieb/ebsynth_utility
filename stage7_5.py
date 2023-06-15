import os
import re
import subprocess
import glob
import shutil
import time
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from tqdm import tqdm

def clamp(n, smallest, largest):
    return sorted([smallest, n, largest])[1]


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


def get_ext(export_type):
    if export_type in ("mp4","webm","gif"):
        return "." + export_type
    else:
        return ".avi"


def trying_to_add_audio(original_movie_path, no_snd_movie_path, output_path, tmp_dir ):
    if os.path.isfile(original_movie_path):
        sound_path = os.path.join(tmp_dir , 'sound.mp4')
        if not Path(sound_path).exists():
            subprocess.call("ffmpeg -i " + original_movie_path + " -vn -acodec copy " + sound_path, shell=True)
        
        if os.path.isfile(sound_path):
            # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
            subprocess.call("ffmpeg -i " + no_snd_movie_path + " -i " + sound_path + " -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 " + output_path, shell=True)
            return True
    
    return False


def ebsynth_utility_stage7_5(dbg, project_dir, original_movie_path, frame_mask_path, back_path, back_mask_path, export_type):

    dbg.print("stage7_5")
    dbg.print("")

    fps = 30
    clip = cv2.VideoCapture(original_movie_path)
    if clip:
        fps = clip.get(cv2.CAP_PROP_FPS)
        clip.release()

    dbg.print("export_type: {}".format(export_type))
    dbg.print("fps: {}".format(fps))
    
    front_frames = Path(project_dir) / "crossfade_tmp"
    back_frames = Path(back_path) / "crossfade_tmp"
    frame_mask_path = Path(frame_mask_path)
    back_mask_path = Path(back_mask_path)

    mixed_crossfade_path = Path(project_dir) / "front_back_crossfade_tmp"
    mixed_crossfade_path.mkdir(exist_ok=True)

    ### create frame imgs
    for front_image_filename in tqdm(front_frames.glob('*.png')):
        front_image = Image.open(str(front_image_filename))
        front_mask_image = Image.open(str(frame_mask_path / front_image_filename.name)).convert('L')

        back_image = Image.open(str(back_frames / front_image_filename.name))
        back_mask_image = Image.open(str(back_mask_path / front_image_filename.name)).convert('L')

        final_image = Image.composite(front_image, back_image, front_mask_image)

        final_image.save(str(mixed_crossfade_path / front_image_filename.name))
    
    ### create movie
    movie_base_name = time.strftime("%Y%m%d-%H%M%S")

    def create_movie_with_sound(frames_path, postfix=''):   
        # movie only from front frames
        start = int(sorted(list(frames_path.glob('*.png')))[0].stem)
        end = int(sorted(list(frames_path.glob('*.png')))[-1].stem)
        number_of_digits = len((list(frames_path.glob('*.png')))[0].stem)
        filename = os.path.join(project_dir , movie_base_name + postfix + get_ext(export_type))
        create_movie_from_frames(frames_path, start, end, number_of_digits, fps, filename, export_type)
        if export_type == "mp4":
            with_snd_path = os.path.join(project_dir , movie_base_name + postfix + '_with_snd.mp4')
            if trying_to_add_audio(original_movie_path, filename, with_snd_path, project_dir):
                dbg.print("exported : " + with_snd_path)

    # movie only from front frames
    create_movie_with_sound(front_frames, postfix='_front')

    # movie only from back frames
    create_movie_with_sound(back_frames, postfix='_back')

    # movie only from with both frames
    create_movie_with_sound(mixed_crossfade_path, postfix='')
    
    dbg.print("")
    dbg.print("completed.")

