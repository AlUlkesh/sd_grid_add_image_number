from modules import scripts
from modules import script_callbacks
from modules.processing import Processed
from modules.shared import opts, OptionInfo
from fonts.ttf import Roboto
from PIL import Image, ImageFont, ImageDraw
import os

# Add option to settings
def on_ui_settings():
    opts.add_option("sd_grid_add_image_number", OptionInfo(True, "Add the image's number to its picture in the grid (when 'Add number to filename' is on)", section=("saving-images", "Saving images/grids")))
script_callbacks.on_ui_settings(on_ui_settings)

# Insert individual image number, lower left corner, in front of a box
def handle_image_grid_loop(img : script_callbacks.ImageGridLoopParams):
    if opts.sd_grid_add_image_number and opts.save_images_add_number and opts.samples_save and hasattr(img, "already_saved_as"):
        img_filename = os.path.basename(img.already_saved_as)
        img_filename_split = img_filename.split('-')
        img_num_text = img_filename_split[0]

        if img_num_text.isdigit():
            img_num_draw = ImageDraw.Draw(img)
            img_num_font = ImageFont.truetype(Roboto, 24)
            img_num_color = (255, 255, 255)
            img_num_box_color = (0, 0, 0)
            img_num_distance = 10

            _, img_num_height = img.size
            img_num_text_width, img_num_text_height = img_num_draw.textsize(img_num_text, font=img_num_font)

            img_num_box_x = img_num_distance
            img_num_box_y = img_num_height - img_num_distance
            img_num_box_width = img_num_text_width + img_num_distance * 2
            img_num_box_height = img_num_text_height + img_num_distance * 2
            img_num_box_x1 = img_num_box_x
            img_num_box_y1 = img_num_box_y - img_num_box_height
            img_num_box_x2 = img_num_box_x + img_num_box_width
            img_num_box_y2 = img_num_box_y

            img_num_x = img_num_box_x + img_num_box_width // 2 - img_num_text_width // 2
            img_num_y = img_num_box_y - img_num_box_height // 2 - img_num_text_height // 2

            img_num_draw.rectangle((img_num_box_x1, img_num_box_y1, img_num_box_x2, img_num_box_y2), fill=img_num_box_color)
            img_num_draw.text((img_num_x, img_num_y), img_num_text, font=img_num_font, fill=img_num_color)
script_callbacks.on_image_grid_loop(handle_image_grid_loop)
