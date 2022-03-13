import sys
import os
import copy
import math
import yaml
import zipfile
from PIL import Image


FOLDER_NAME = len(sys.argv) >= 2 and sys.argv[1]
assert type(FOLDER_NAME) == str, "No folder name provided"

FOLDER_NAME += "/"
EXISTING_FONTS_PATH = FOLDER_NAME + "existing_fonts.yaml"
OUTPUT_FOLDER = FOLDER_NAME + "output/"

MAX_CODE_POINT = 1114111
EXIST_CODE_POINTS = {}
RESERVED_CODE_POINTS = []

SETTINGS = {
    "code_point_start": 983200,
    "code_point_step": 1,
    "resize_to": 52,
    "padding": 2,
    "zip_fname": "font.zip"
}

try:
    with open(FOLDER_NAME + "settings.yaml", "r") as stream:
        existing_fonts = yaml.safe_load(stream)
        if existing_fonts is not None:
            for key in existing_fonts:
                SETTINGS[key] = existing_fonts[key]
except:
    print("Can't load settings file, use default settings instead")

try:
    with open(EXISTING_FONTS_PATH, "r") as stream:
        existing_fonts = yaml.safe_load(stream)
        if existing_fonts is not None:
            for name in existing_fonts:
                EXIST_CODE_POINTS[name] = existing_fonts[name]
            RESERVED_CODE_POINTS = EXIST_CODE_POINTS.values()
except:
    pass

PADDING = SETTINGS["padding"]
HALF_PADDING = PADDING // 2
SPACING = SETTINGS["resize_to"] + PADDING
RESIZE_SIZE = [SETTINGS["resize_to"], SETTINGS["resize_to"]]

# sys.exit()

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


valid_image_formats = [ "png", "jpg", "jpeg" ]
image_list = []
for fname in os.listdir(FOLDER_NAME):
    for suffix in valid_image_formats:
        if fname.endswith("." + suffix):
            image_list.append(fname)
            break

assert len(image_list) <= (2 ** 13 / SPACING) ** 2, "Too Many Images !"

final_img = get_final_image(image_list, SPACING)
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

code_point = SETTINGS["code_point_start"] - SETTINGS["code_point_step"]

def get_code_point_for_name(name):
    global code_point
    exist_code_point = EXIST_CODE_POINTS.get(name)
    if exist_code_point is not None:
        return exist_code_point
    else:
        code_point += SETTINGS["code_point_step"]
        if code_point not in RESERVED_CODE_POINTS:
            return code_point
        else:
            while code_point in RESERVED_CODE_POINTS:
                code_point += SETTINGS["code_point_step"]
                assert code_point <= MAX_CODE_POINT, "Can't get any valid code point to use"
            return code_point


pos = [HALF_PADDING, HALF_PADDING]

for fname in image_list:

    im = expand2square(Image.open(FOLDER_NAME + fname)).resize(RESIZE_SIZE)

    if pos[0] + im.size[0] + HALF_PADDING > final_img.size[0]:
        pos[0] = HALF_PADDING
        pos[1] += RESIZE_SIZE[1] + PADDING

    final_img.paste(im, copy.copy(pos))

    name = os.path.splitext(fname)[0]
    code = get_code_point_for_name(name)
    fnt_final = fnt_final + fnt_temp.format(code, pos[0] - HALF_PADDING, pos[1] - HALF_PADDING, RESIZE_SIZE[0], RESIZE_SIZE[1], RESIZE_SIZE[0] - PADDING)
    lua_final = lua_final + lua_temp.format(name, chr(code))

    pos[0] += RESIZE_SIZE[0] + PADDING
    EXIST_CODE_POINTS[name] = code


if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

final_img.save(OUTPUT_FOLDER + "font.png")
with open(OUTPUT_FOLDER + "font.fnt", "w", encoding = "utf-8") as out:
    fnt_final = '  <chars count="{}">\n'.format(len(image_list)) + fnt_final + fnt_tail
    fnt_final = fnt_head.format(RESIZE_SIZE[0] - PADDING, RESIZE_SIZE[0] - PADDING, final_img.size[0], final_img.size[1]) + fnt_final
    out.write(fnt_final)

with open(OUTPUT_FOLDER + "nitro_emojis.lua", "w", encoding = "utf-8") as out:
    lua_final = 'return {\n' + lua_final + '}\n'
    out.write(lua_final)


if "tex_convert_cmd" in SETTINGS:
    os.system(SETTINGS["tex_convert_cmd"].format(OUTPUT_FOLDER + "font.png"))
    with zipfile.ZipFile(OUTPUT_FOLDER + SETTINGS["zip_fname"], "w", zipfile.ZIP_DEFLATED) as outzip:
        outzip.write(OUTPUT_FOLDER + "font.tex", "font.tex")
        outzip.write(OUTPUT_FOLDER + "font.fnt", "font.fnt")

with open(EXISTING_FONTS_PATH, 'w') as outfile:
    yaml.dump(EXIST_CODE_POINTS, outfile, default_flow_style=False)
