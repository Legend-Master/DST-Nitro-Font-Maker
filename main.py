import sys
import os
import copy
import math
import yaml
from PIL import Image


FOLDER_NAME = len(sys.argv) >= 2 and sys.argv[1]
assert type(FOLDER_NAME) == str, "No folder name provided"
FOLDER_NAME += "/"

settings = {
    "code_point_start": 983200,
    "code_point_step": 1,
    "resize_to": 52,
    "padding": 2
}

try:
    with open(FOLDER_NAME + "settings.yaml", "r") as stream:
        settings_file = yaml.safe_load(stream)
        if settings_file is not None:
            for key in settings_file:
                settings[key] = settings_file[key]
except:
    print("Can't load settings file, use default settings instead")


def expand2square(pil_img, background_color=(255, 255, 255, 0)):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


def get_final_image(image_list, spacing):
    size = None
    for i in range(6, 13):
        lenth = 2 ** i
        if lenth > math.ceil((math.sqrt(len(image_list)))) * spacing:
            size = (lenth, lenth)
            break
    return size and Image.new("RGBA", size)


padding = settings["padding"]
spacing = settings["resize_to"] + padding

valid_image_formats = [ "png", "jpg", "jpeg" ]
image_list = []
for fname in os.listdir(FOLDER_NAME):
    for suffix in valid_image_formats:
        if fname.endswith("." + suffix):
            image_list.append(fname)
            break

assert len(image_list) <= (2 ** 13 / spacing) ** 2, "Too Many Images !"

final_img = get_final_image(image_list, spacing)
assert final_img, "Can't get final image"

fnt_final = ""
fnt_head = '''<?xml version="1.0"?>
<font>
  <info face="emoji set" size="{}" bold="1" italic="0" charset="" unicode="1" stretchH="100" smooth="1" aa="1" padding="1,1,1,1" spacing="2,2" outline="0"/>
  <common lineHeight="{}" base="41" scaleW="{}" scaleH="{}" pages="1" packed="0" alphaChnl="1" redChnl="0" greenChnl="0" blueChnl="0"/>
  <pages>
    <page id="0" file="emoji_0.png" />
  </pages>
'''
fnt_temp = '    <char id="{}" x="{}" y="{}" width="{}" height="{}" xoffset="-1" yoffset="-1" xadvance="{}" page="0" chnl="15" />\n'
fnt_tail = '''  </chars>
</font>
'''

lua_final = ""
lua_temp = '    ["{}"] = "{}",\n'

resize_size = [settings["resize_to"], settings["resize_to"]]
half_padding = padding // 2
pos = [half_padding, half_padding]

code_point = settings["code_point_start"]

for fname in image_list:

    im = expand2square(Image.open(FOLDER_NAME + fname)).resize(resize_size)

    if pos[0] + im.size[0] + half_padding > final_img.size[0]:
        pos[0] = half_padding
        pos[1] += resize_size[1] + padding

    final_img.paste(im, copy.copy(pos))
    fnt_final = fnt_final + fnt_temp.format(code_point, pos[0] - half_padding, pos[1] - half_padding, resize_size[0], resize_size[1], resize_size[0] - padding)
    lua_final = lua_final + lua_temp.format(os.path.splitext(fname)[0], chr(code_point))

    pos[0] += resize_size[0] + padding
    code_point += settings["code_point_step"]

OUTPUT_FOLDER = FOLDER_NAME + "output/"
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

final_img.save(OUTPUT_FOLDER + "font.png")
with open(OUTPUT_FOLDER + "font.fnt", "w", encoding = "utf-8") as out:
    fnt_final = '  <chars count="{}">\n'.format(len(image_list)) + fnt_final + fnt_tail
    fnt_final = fnt_head.format(resize_size[0] - padding, resize_size[0] - padding, final_img.size[0], final_img.size[1]) + fnt_final
    out.write(fnt_final)
with open(OUTPUT_FOLDER + "nitro_emojis.lua", "w", encoding = "utf-8") as out:
    lua_final = 'return {\n' + lua_final + '}\n'
    out.write(lua_final)
