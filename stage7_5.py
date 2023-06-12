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
        subprocess.call("ffmpeg -i " + original_movie_path + " -vn -acodec copy " + sound_path, shell=True)
        
        if os.path.isfile(sound_path):
            # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4

            subprocess.call("ffmpeg -i " + no_snd_movie_path + " -i " + sound_path + " -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 " + output_path, shell=True)
            return True
    
    return False


def ebsynth_utility_stage7_5(dbg, blend_rate, project_dir, original_movie_path, frame_mask_path, back_path, back_mask_path, export_type):

    dbg.print("stage7_5")
    dbg.print("")

    fps = 30
    clip = cv2.VideoCapture(original_movie_path)
    if clip:
        fps = clip.get(cv2.CAP_PROP_FPS)
        clip.release()
    
    blend_rate = clamp(blend_rate, 0.0, 1.0)
    dbg.print("export_type: {}".format(export_type))
    dbg.print("fps: {}".format(fps))
    
    front_frames = Path(project_dir) / "crossfade_tmp"
    back_frames = Path(back_path) / "crossfade_tmp"
    frame_mask_path = Path(frame_mask_path)
    back_mask_path = Path(back_mask_path)

    mixed_crossfade_path = os.path.join( project_dir , "front_back_crossfade_tmp") 

    ### create frame imgs
    for front_image_filename in front_frames.glob('*.png'):
        front_image = Image.open(str(front_image_filename))
        front_mask_image = Image.open(str(frame_mask_path / front_image_filename.name)).conver('L')

        back_image = Image.open(str(back_frames / front_image_filename.name))
        back_mask_image = Image.open(str(back_mask_path / front_image_filename.name)).conver('L')

        print(np.array(front_image)[0][0])
        print(np.array(front_mask_image)[0][0])
        print(np.array(back_image)[0][0])
        print(np.array(back_mask_image)[0][0])
        raise
    
    ### create movie
    movie_base_name = time.strftime("%Y%m%d-%H%M%S")
    if is_invert_mask:
        movie_base_name = "inv_" + movie_base_name
    
    nosnd_path = os.path.join(project_dir , movie_base_name + get_ext(export_type))
    
    start = out_dirs[0]['startframe']
    end = out_dirs[-1]['endframe']

    create_movie_from_frames( tmp_dir, start, end, number_of_digits, fps, nosnd_path, export_type)

    dbg.print("exported : " + nosnd_path)
    
    if export_type == "mp4":

        with_snd_path = os.path.join(project_dir , movie_base_name + '_with_snd.mp4')

        if trying_to_add_audio(original_movie_path, nosnd_path, with_snd_path, tmp_dir):
            dbg.print("exported : " + with_snd_path)
    
    dbg.print("")
    dbg.print("completed.")

