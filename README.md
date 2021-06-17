# DST Nitro Font Maker

A tool for generating font files for Don't Starve Together mod [DST Nitro](https://steamcommunity.com/sharedfiles/filedetails/?id=2248952715)

## Requirement
  Python3, yaml, PIL

## Usage
  Put all your images in to a folder then use `python main.py <folder>` to generate font.png, font.fnt, nitro_emojis.lua
  Put a settings.yaml in the folder to change the settings

## Settings

  - `code_point_start`: int, config which code point should we start with ( default: 983200 )
  - `code_point_step`: int, code point steps to next image ( default: 1 )
  - `resize_to`: int, resize to (resize_to, resize_to) for every image ( default: 52 ) ( highly recommended using a number powered by 2 )
  - `tex_convert_cmd`: str, cmd for convert .png file to .tex file ( default: None )
  - `zip_fname`: str, final zip's file name ( default: font.zip ) ( only used when `tex_convert_cmd` is declared )
