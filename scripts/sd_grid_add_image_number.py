from modules import scripts
from modules import script_callbacks
from modules.processing import Processed
from modules.shared import opts, OptionInfo, state
from fonts.ttf import Roboto
from PIL import Image, ImageFont, ImageDraw
import modules.sd_vae
import os

xyz_infos = {}
default_font_size = 24
min_font_size = 14

xyz_options = {
    "Nothing": None,
    "Seed": "seed",
    "Var. seed": "subseed",
    "Var. strength": "subseed_strength",
    "Steps": "steps",
    "Hires steps": "hr_second_pass_steps",
    "CFG Scale": "cfg_scale",
    "Image CFG Scale": "image_cfg_scale",
    "Prompt S/R": None,
    "Prompt order": None,
    "Sampler": "sampler_name",
    "Checkpoint name": "#1",
    "Sigma Churn": "s_churn",
    "Sigma min": "s_tmin",
    "Sigma max": "s_tmax",
    "Sigma noise": "s_noise",
    "Eta": "eta",
    "Clip skip": "#2",
    "Denoising": "denoising_strength",
    "Hires upscaler": None,
    "Cond. Image Mask Weight": "inpainting_mask_weight",
    "VAE": "#3",
    "Styles": None
}

# Add option to settings
def on_ui_settings():
    opts.add_option("sd_grid_add_image_number", OptionInfo(True, "Add the image's number to its picture in the grid (when 'Add number to filename' is on)", section=("saving-images", "Saving images/grids")))
    opts.add_option("sd_grid_add_xyz_info", OptionInfo(False, "Add X/Y/Z script info to its picture in the grid", section=("saving-images", "Saving images/grids")))
script_callbacks.on_ui_settings(on_ui_settings)

def getaxis_value(p, img_filename, getaxis):
    global xyz_infos
    axis_value = None
    if hasattr(state, getaxis):
        axis_option = xyz_options[getattr(getattr(state, getaxis), "axis").label]
        if axis_option == "#1":
            axis_value = os.path.basename(p.sd_model.sd_model_checkpoint)
        elif axis_option == "#2":
            axis_value = opts.CLIP_stop_at_last_layers
        elif axis_option == "#3":
            axis_value = os.path.basename(modules.sd_vae.loaded_vae_file)
        elif axis_option is not None:
            axis_value = getattr(p, axis_option)
    xyz_infos[img_filename][getaxis] = axis_value

def handle_image_saved(params : script_callbacks.ImageSaveParams):
    global xyz_infos
    if opts.sd_grid_add_xyz_info:
        if hasattr(params.image, "already_saved_as"):
            img_filename = params.image.already_saved_as
            xyz_infos[img_filename] = {}
            getaxis_value(params.p, img_filename, "xyz_plot_x")
            getaxis_value(params.p, img_filename, "xyz_plot_y")
            getaxis_value(params.p, img_filename, "xyz_plot_z")

script_callbacks.on_image_saved(handle_image_saved)

def img_write(img_num_draw, img_text, img_num_box_width, img_num_text_width, img_num_box_height, img_num_text_height, img_num_box_x1, img_num_box_y1, img_num_box_color, img_num_font, img_num_color, img_num_distance, img_num_width, img_num_height):
    img_num_box_x2 = img_num_box_x1 + img_num_box_width
    img_num_box_y2 = img_num_box_y1 + img_num_box_height
    img_num_x = img_num_box_x1 + img_num_distance
    img_num_y = img_num_box_y1 + img_num_distance

    if (img_num_box_x1 < img_num_distance or
        img_num_box_y1 < img_num_distance or
        img_num_box_x2 > img_num_width - img_num_distance or
        img_num_box_y2 > img_num_height - img_num_distance):
        no_fit = True
    else:
        no_fit = False
        img_num_draw.rectangle((img_num_box_x1, img_num_box_y1, img_num_box_x2, img_num_box_y2), fill=img_num_box_color)
        img_num_draw.text((img_num_x, img_num_y), img_text, font=img_num_font, fill=img_num_color)

    return img_num_draw, no_fit

def text_corner(corner, img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width):
    no_fit = True
    removed_key = False
    current_font_size = default_font_size
    while no_fit:
        img_num_font = ImageFont.truetype(Roboto, current_font_size)
        img_num_text_width, img_num_text_height = img_num_draw.textsize(img_text, font=img_num_font)
        if corner == "bottom_left":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = bottom_left(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height)
        if corner == "top_left":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = top_left(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height)
        if corner == "top_right":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = top_right(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height)
        if corner == "bottom_right":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = bottom_right(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height)
        img_num_draw, no_fit = img_write(img_num_draw, img_text, img_num_box_width, img_num_text_width, img_num_box_height, img_num_text_height, img_num_box_x1, img_num_box_y1, img_num_box_color, img_num_font, img_num_color, img_num_distance, img_num_width, img_num_height)
        if no_fit:
            if current_font_size <= min_font_size:
                if removed_key:
                    print(f'Text for "{img_text}" does not fit on image')
                    no_fit = False
                else:
                    img_text = img_text.split(": ", 1)[1]
                    current_font_size = default_font_size
                    removed_key = True
            else:
                current_font_size = current_font_size - 1

    return img_num_draw

def bottom_left(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_distance
    img_num_box_y1 = img_num_height - img_num_distance - img_num_box_height

    return img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1

def top_left(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_distance
    img_num_box_y1 = img_num_distance

    return img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1

def top_right(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_width - img_num_text_width - img_num_distance * 3
    img_num_box_y1 = img_num_text_height + img_num_distance * 2

    return img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1

def bottom_right(img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_width - img_num_text_width - img_num_distance * 3
    img_num_box_y1 = img_num_height - img_num_text_height * 2 - img_num_distance * 4

    return img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1

# Insert individual image infos, in corners, in front of a box
def handle_image_grid(params : script_callbacks.ImageGridLoopParams):
    if opts.sd_grid_add_image_number or opts.sd_grid_add_xyz_info:
        for img in params.imgs:
            if hasattr(img, "already_saved_as"):
                img_filename = img.already_saved_as
                img_filename_base = os.path.basename(img.already_saved_as)
                img_filename_split = img_filename_base.split('-')
                img_num_text = img_filename_split[0]

                if img_num_text != "grid":
                    img_num_draw = ImageDraw.Draw(img)
                    img_num_color = (255, 255, 255)
                    img_num_box_color = (0, 0, 0)
                    img_num_distance = 10

                    img_num_width, img_num_height = img.size
                
                    if opts.sd_grid_add_image_number and opts.save_images_add_number and opts.samples_save and img_num_text.isdigit():
                        img_text = img_num_text
                        img_num_draw = text_corner("bottom_left", img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width)
                    try:
                        if opts.sd_grid_add_xyz_info and (xyz_infos[img_filename]["xyz_plot_x"] is not None or xyz_infos[img_filename]["xyz_plot_y"] is not None or xyz_infos[img_filename]["xyz_plot_z"] is not None):
                            if xyz_infos[img_filename]["xyz_plot_x"] is not None:
                                img_xyz_axis = f"{state.xyz_plot_x.axis.label}: {xyz_infos[img_filename]['xyz_plot_x']}"
                                img_text = img_xyz_axis
                                img_num_draw = text_corner("top_left", img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width)
                            if xyz_infos[img_filename]["xyz_plot_y"] is not None:
                                img_xyz_axis = f"{state.xyz_plot_y.axis.label}: {xyz_infos[img_filename]['xyz_plot_y']}"
                                img_text = img_xyz_axis
                                img_num_draw = text_corner("top_right", img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width)
                            if xyz_infos[img_filename]["xyz_plot_z"] is not None:
                                img_xyz_axis = f"{state.xyz_plot_z.axis.label}: {xyz_infos[img_filename]['xyz_plot_z']}"
                                img_text = img_xyz_axis
                                img_num_draw = text_corner("bottom_right", img_text, img_num_draw, img_num_distance, img_num_height, img_num_box_color, img_num_color, img_num_width)
                    except KeyError:
                        pass
                                           
script_callbacks.on_image_grid(handle_image_grid)
