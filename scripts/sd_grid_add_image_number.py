import os
import types

from PIL import Image, ImageDraw

import modules.sd_vae
from modules import script_callbacks
from modules.images import get_font
from modules.shared import OptionInfo, opts, state
from scripts.xyz_grid import axis_options

xyz_infos = {}
default_font_size = 24
min_font_size = 9 # reduced the minimum font size to try and avoid overlapping textboxes

# Add option to settings
def on_ui_settings():
    img_num_section = "saving-images"
    img_num_section_name = img_num_section

    for key, opt in opts.data_labels.items():
        if opt.section[0] == img_num_section:
            img_num_section_name = opt.section[1]
            break

    opts.add_option("sd_grid_add_image_number", OptionInfo(True, "Add the image's number to its picture in the grid (when 'Add number to filename' is on)", section=(img_num_section, img_num_section_name)))
    opts.add_option("sd_grid_add_xyz_info", OptionInfo(False, "Add X/Y/Z script info to its picture in the grid", section=(img_num_section, img_num_section_name)))
script_callbacks.on_ui_settings(on_ui_settings)

def getaxis_infos(p, current_axis):
    current_axis_label = current_axis.axis.label
    current_axis_key = None
    current_axis_value = None
    for option in axis_options:
        if option.label == current_axis_label:
            get_from = "p"
            if isinstance(option.apply, types.FunctionType):
                if option.apply.__name__ == "<lambda>":
                    current_axis_key = option.apply.__code__.co_consts[1]
                elif option.apply.__name__ == "fun" and option.apply.__closure__ is not None:
                    if len(option.apply.__closure__) == 1:
                        # For example "apply_field"
                        current_axis_key = option.apply.__closure__[0].cell_contents
                    elif len(option.apply.__closure__) == 2:
                        # For example "apply_override"
                        current_axis_key = option.apply.__closure__[1].cell_contents
                # Different key-names in xyz and p/opts
                elif option.apply.__name__ == "apply_checkpoint":
                    current_axis_key = "sd_model_name"
                elif option.apply.__name__ == "apply_vae":
                    current_axis_key = "sd_vae_name"
                elif option.apply.__name__ == "apply_face_restore":
                    current_axis_key = "face_restoration_model"
                elif option.apply.__name__ == "apply_styles":
                    get_from = "p0"
                    current_axis_key = "styles"
                elif option.apply.__name__ == "apply_clip_skip":
                    get_from = "opts"
                    current_axis_key = "CLIP_stop_at_last_layers"
                elif option.apply.__name__ == "apply_uni_pc_order":
                    get_from = "opts"
                    current_axis_key = "uni_pc_order"
            elif isinstance(option.apply, types.MethodType):
                current_axis_key = option.apply.__func__.__code__.co_consts[1]
            else:
                current_axis_key = None
            break
    if current_axis_key is not None:
        if get_from == "p":
            if hasattr(p, current_axis_key):
                current_axis_value = getattr(p, current_axis_key)
        if get_from == "p0":
            if hasattr(p, current_axis_key):
                current_axis_value = getattr(p, current_axis_key)[0]
        elif get_from == "opts":
            if hasattr(opts, current_axis_key):
                current_axis_value = getattr(opts, current_axis_key)
        
    return current_axis_label, current_axis_key, current_axis_value

def get_img_num_text(img_filename):
    img_filename_base = os.path.basename(img_filename)
    img_filename_split = img_filename_base.split('-')
    img_num_text = img_filename_split[0]

    if img_num_text.endswith("grid"):
        img_num_text = None

    return img_num_text

def handle_image_saved(params : script_callbacks.ImageSaveParams):
    global xyz_infos
    if opts.sd_grid_add_xyz_info:
        if hasattr(params.image, "already_saved_as"):
            img_filename = params.image.already_saved_as
            img_num_text = get_img_num_text(img_filename)

            if img_num_text != None:
                try:
                    img_label_x, img_key_x, img_value_x = getaxis_infos(params.p, state.xyz_plot_x)
                    img_label_y, img_key_y, img_value_y = getaxis_infos(params.p, state.xyz_plot_y)
                    img_label_z, img_key_z, img_value_z = getaxis_infos(params.p, state.xyz_plot_z)
                    xyz_infos[img_filename] = {
                        "img_label_x": img_label_x,
                        "img_key_x": img_key_x,
                        "img_value_x": img_value_x,
                        "img_label_y": img_label_y,
                        "img_key_y": img_key_y,
                        "img_value_y": img_value_y,
                        "img_label_z": img_label_z,
                        "img_key_z": img_key_z,
                        "img_value_z": img_value_z
                    }
                except AttributeError:
                    xyz_infos[img_filename] = {
                        "img_label_x": None,
                        "img_key_x": None,
                        "img_value_x": None,
                        "img_label_y": None,
                        "img_key_y": None,
                        "img_value_y": None,
                        "img_label_z": None,
                        "img_key_z": None,
                        "img_value_z": None
                    }
                
script_callbacks.on_image_saved(handle_image_saved)

def img_write(img, img_text, img_num_box_width, img_num_box_height, img_num_box_x1, img_num_box_y1, img_num_font, img_num_distance, img_num_width, img_num_height):
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
        img = img.convert("RGBA")
        # White background, fully transparent
        overlay = Image.new("RGBA", (img_num_width, img_num_height), (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        # Black box, half transparent
        overlay_draw.rectangle((img_num_box_x1, img_num_box_y1, img_num_box_x2, img_num_box_y2), fill=(0, 0, 0, 127))
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")
        img_num_draw = ImageDraw.Draw(img)
        img_num_draw.text((img_num_x, img_num_y), img_text, font=img_num_font, fill=(255, 255, 255))

    return img, no_fit

def text_corner(corner, img_text, img, img_num_distance, img_num_height, img_num_width):
    no_fit = True
    removed_key = False
    current_font_size = default_font_size
    while no_fit:
        img_num_draw = ImageDraw.Draw(img)
        img_num_font = get_font(current_font_size)
        img_num_text_width, img_num_text_height = img_num_draw.textsize(img_text, font=img_num_font)
        if corner == "bottom_left":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = bottom_left(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height)
        if corner == "top_left":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = top_left(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height)
        if corner == "top_right":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = top_right(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height)
        if corner == "bottom_right":
            img_num_box_width,  img_num_box_height, img_num_box_x1, img_num_box_y1 = bottom_right(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height)
        img, no_fit = img_write(img, img_text, img_num_box_width, img_num_box_height, img_num_box_x1, img_num_box_y1, img_num_font, img_num_distance, img_num_width, img_num_height)
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

    return img

def bottom_left(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_distance
    img_num_box_y1 = img_num_height - img_num_distance - img_num_box_height

    return img_num_box_width, img_num_box_height, img_num_box_x1, img_num_box_y1

def top_left(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_distance
    img_num_box_y1 = img_num_distance

    return img_num_box_width, img_num_box_height, img_num_box_x1, img_num_box_y1

def top_right(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_width - img_num_text_width - img_num_distance * 3
    img_num_box_y1 = img_num_text_height + img_num_distance * 2

    return img_num_box_width, img_num_box_height, img_num_box_x1, img_num_box_y1

def bottom_right(img_text, img_num_distance, img_num_height, img_num_width, img_num_text_width, img_num_text_height):
    img_num_box_width = img_num_text_width + img_num_distance * 2
    img_num_box_height = img_num_text_height + img_num_distance * 2
    img_num_box_x1 = img_num_width - img_num_text_width - img_num_distance * 3
    img_num_box_y1 = img_num_height - img_num_text_height * 2 - img_num_distance * 4

    return img_num_box_width, img_num_box_height, img_num_box_x1, img_num_box_y1

# Insert individual image infos, in corners, in front of a box
def handle_image_grid(params : script_callbacks.ImageGridLoopParams):
    if opts.sd_grid_add_image_number or opts.sd_grid_add_xyz_info:
        for i, img in enumerate(params.imgs):
            if hasattr(img, "already_saved_as"):
                img_filename = img.already_saved_as
                img_num_text = get_img_num_text(img_filename)

                if img_num_text != None:
                    img_num_distance = 10

                    img_num_width, img_num_height = img.size
                
                    if opts.sd_grid_add_image_number and opts.save_images_add_number and opts.samples_save and img_num_text.isdigit():
                        img_text = img_num_text
                        img = text_corner("bottom_left", img_text, img, img_num_distance, img_num_height, img_num_width)
                    try:
                        if opts.sd_grid_add_xyz_info:
                            img_label = xyz_infos[img_filename].get("img_label_x")
                            img_key = xyz_infos[img_filename].get("img_key_x")
                            img_value = xyz_infos[img_filename].get("img_value_x")
                            if img_label is not None and img_key is not None and img_value is not None:
                                if img_label != "Nothing":
                                    img_text = f'{img_label}: {img_value}'
                                    img = text_corner("top_left", img_text, img, img_num_distance, img_num_height, img_num_width)
                            img_label = xyz_infos[img_filename].get("img_label_y")
                            img_key = xyz_infos[img_filename].get("img_key_y")
                            img_value = xyz_infos[img_filename].get("img_value_y")
                            if img_label is not None and img_key is not None and img_value is not None:
                                if img_label != "Nothing":
                                    img_text = f'{img_label}: {img_value}'
                                img = text_corner("top_right", img_text, img, img_num_distance, img_num_height, img_num_width)
                            img_label = xyz_infos[img_filename].get("img_label_z")
                            img_key = xyz_infos[img_filename].get("img_key_z")
                            img_value = xyz_infos[img_filename].get("img_value_z")
                            if img_label is not None and img_key is not None and img_value is not None:
                                if img_label != "Nothing":
                                    img_text = f'{img_label}: {img_value}'
                                img = text_corner("bottom_right", img_text, img, img_num_distance, img_num_height, img_num_width)
                    except KeyError:
                        pass
                    params.imgs[i] = img
script_callbacks.on_image_grid(handle_image_grid)

