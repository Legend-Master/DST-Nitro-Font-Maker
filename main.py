import math
import os
import sys
import zipfile

import yaml
from PIL import Image

SETTINGS = {
    "code_point_start": 983200,
    "code_point_step": 1,
    "resize_to": 52,
    "padding": 2,
    "zip_fname": "font.zip"
}

MAX_CODE_POINT = 1114111
EXIST_CODE_POINTS = {}
RESERVED_CODE_POINTS = []

FNT_HEAD = '''<?xml version="1.0"?>
<font>
  <info face="emoji set" size="{}" bold="1" italic="0" charset="" unicode="1" stretchH="100" smooth="1" aa="1" padding="1,1,1,1" spacing="2,2" outline="0"/>
  <common lineHeight="{}" base="41" scaleW="{}" scaleH="{}" pages="1" packed="0" alphaChnl="1" redChnl="0" greenChnl="0" blueChnl="0"/>
  <pages>
    <page id="0" file="emoji_0.png" />
  </pages>
    <chars count="{}">
'''
FNT_TEMPLATE = '    <char id="{}" x="{}" y="{}" width="{}" height="{}" xoffset="-1" yoffset="-1" xadvance="{}" page="0" chnl="15" />\n'
FNT_TAIL = '''  </chars>
</font>
'''

LUA_TEMPLATE = '    ["{}"] = "{}",\n'


def expand_to_square(img):
    width, height = img.size
    if width == height:
        return img
    elif width > height:
        result = Image.new("RGBA", (width, width))
        result.paste(img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new("RGBA", (height, height))
        result.paste(img, ((height - width) // 2, 0))
        return result


def get_final_image(image_count, spacing):
    target_length = math.ceil(math.sqrt(image_count)) * spacing
    # 64 ~ 8192
    for i in range(6, 13):
        length = 2 ** i
        if length > target_length:
            size = (length, length)
            return Image.new("RGBA", size)


def get_code_point_for_name(name):
    global current_code_point
    exist_code_point = EXIST_CODE_POINTS.get(name)
    if exist_code_point is not None:
        return exist_code_point
    else:
        current_code_point += SETTINGS["code_point_step"]
        while current_code_point in RESERVED_CODE_POINTS:
            current_code_point += SETTINGS["code_point_step"]
            assert current_code_point <= MAX_CODE_POINT, "Can't get any valid code point to use"
        return current_code_point


def load_settings_file():
    settings_file_path = os.path.join(FOLDER_NAME, "settings.yaml")
    if os.path.exists(settings_file_path):
        try:
            with open(settings_file_path, "r") as stream:
                settings_override = yaml.safe_load(stream)
                if settings_override is not None:
                    for key in settings_override:
                        SETTINGS[key] = settings_override[key]
        except:
            print("Can't load settings file, use default settings instead")
    # else:
    #     print("Don't have settings file, use default settings instead")


def load_existing_fonts():
    try:
        global RESERVED_CODE_POINTS
        with open(EXISTING_FONTS_PATH, "r") as stream:
            existing_fonts = yaml.safe_load(stream)
            if existing_fonts is not None:
                for name in existing_fonts:
                    EXIST_CODE_POINTS[name] = existing_fonts[name]
                RESERVED_CODE_POINTS = EXIST_CODE_POINTS.values()
    except:
        pass


def main():
    Image.init()
    image_files = {}
    for file_name in os.listdir(FOLDER_NAME):
        name, ext = os.path.splitext(file_name)
        if ext in Image.EXTENSION:
            image_files[name] = os.path.join(FOLDER_NAME, file_name)

    assert len(image_files) <= (2 ** 13 / SPACING) ** 2, "Too Many Images !"

    final_img = get_final_image(len(image_files), SPACING)
    assert final_img, "Can't get final image"

    x = HALF_PADDING
    y = HALF_PADDING
    fnt_out = {}  # Sort required
    lua_out = ""  # Will be sorted by the next loop

    for name, path in sorted(image_files.items()):

        img = expand_to_square(Image.open(path)).resize(RESIZE_SIZE)

        if x + img.size[0] + HALF_PADDING > final_img.size[0]:
            x = HALF_PADDING
            y += RESIZE_SIZE[1] + PADDING

        final_img.paste(img, (x, y))

        code = get_code_point_for_name(name)
        fnt_out[code] = FNT_TEMPLATE.format(code, x - HALF_PADDING, y - HALF_PADDING, RESIZE_SIZE[0], RESIZE_SIZE[1], RESIZE_SIZE[0] - PADDING)
        lua_out += LUA_TEMPLATE.format(name, chr(code))

        x += RESIZE_SIZE[0] + PADDING
        EXIST_CODE_POINTS[name] = code

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Output .png
    final_img.save(os.path.join(OUTPUT_FOLDER, "font.png"))

    # Output .fnt
    with open(os.path.join(OUTPUT_FOLDER, "font.fnt"), "w", encoding="utf-8") as out:
        out.write(
            FNT_HEAD.format(RESIZE_SIZE[0] - PADDING, RESIZE_SIZE[0] - PADDING, final_img.size[0], final_img.size[1], len(image_files))
            + "".join(value for _, value in sorted(fnt_out.items()))
            + FNT_TAIL
        )

    # Output .lua
    with open(os.path.join(OUTPUT_FOLDER, "nitro_emojis.lua"), "w", encoding="utf-8") as out:
        lua_out = 'return {\n' + lua_out + '}\n'
        out.write(lua_out)

    # Output font zip (font.tex + font.fnt)
    should_zip = True
    if "tex_convert_cmd" in SETTINGS:  # Backward compatible
        os.system(SETTINGS["tex_convert_cmd"].format(os.path.join(OUTPUT_FOLDER, "font.png")))
    elif "tex_convert_args" in SETTINGS:
        import subprocess
        args = list(SETTINGS["tex_convert_args"])
        args.append(os.path.join(OUTPUT_FOLDER, "font.png"))
        subprocess.run(args)
    else:
        should_zip = False

    if should_zip:
        with zipfile.ZipFile(os.path.join(OUTPUT_FOLDER, SETTINGS["zip_fname"]), "w", zipfile.ZIP_DEFLATED) as out_zip:
            out_zip.write(os.path.join(OUTPUT_FOLDER, "font.tex"), "font.tex")
            out_zip.write(os.path.join(OUTPUT_FOLDER, "font.fnt"), "font.fnt")

    # Output existing_fonts.yaml
    with open(EXISTING_FONTS_PATH, 'w') as outfile:
        yaml.dump(EXIST_CODE_POINTS, outfile, default_flow_style=False)


if __name__ == '__main__':

    first_arg = len(sys.argv) >= 2 and sys.argv[1]
    assert type(first_arg) == str, "No folder name provided"

    FOLDER_NAME = os.path.abspath(first_arg)

    EXISTING_FONTS_PATH = os.path.join(FOLDER_NAME, "existing_fonts.yaml")
    OUTPUT_FOLDER = os.path.join(FOLDER_NAME, "output")

    load_settings_file()
    load_existing_fonts()

    PADDING = SETTINGS["padding"]
    HALF_PADDING = PADDING // 2
    SPACING = SETTINGS["resize_to"] + PADDING
    RESIZE_SIZE = (SETTINGS["resize_to"], SETTINGS["resize_to"])

    current_code_point = SETTINGS["code_point_start"] - SETTINGS["code_point_step"]

    main()
