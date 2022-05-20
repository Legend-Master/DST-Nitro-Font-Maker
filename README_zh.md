# DST Nitro 字体生成器

为饥荒联机版 mod [DST Nitro](https://steamcommunity.com/sharedfiles/filedetails/?id=2248952715) 生成字体文件的工具。

## 前置需求

  Python >= 3.6, PyYaml, Pillow

## 使用方法

  将你的所有图像放进文件夹，然后执行 `python main.py <对应文件夹>` 以生成 `font.png`、`font.fnt`、`nitro_emojis.lua`；
  在文件夹内添加 `settings.yaml` 以更改设置。

## 设置文件（settings.yaml）

  - `code_point_start`: int, 第一个图片对应的 unicode 值。( default: 983200 )
  - `code_point_step`: int, 每个图片相比前一个图片增加的 unicode 值。( default: 1 )
  - `resize_to`: int, 将图片缩放到置顶大小 ( default: 52 ) ( 强烈建议设置为 2 的指数级 )
  - `tex_convert_cmd`: str, 执行转换 .png 为 .tex 的脚本位置 ( default: None )
  - `zip_fname`: str, 生成的 zip 文件名称 ( default: font.zip ) ( 仅当设置了 `tex_convert_cmd` 时生效 )
