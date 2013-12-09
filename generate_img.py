#!/usr/bin/env python2
# coding: UTF-8


from os import walk, path, makedirs
import argparse

import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

import wand
import wand.color
import wand.drawing
import wand.image
# from wand.drawing import Drawing
# from wand.image import Image

import fontforge


DOCS_DIR='documents'
FONT_DIR='/usr/share/fonts/'

IMAGE_EXT='png'

FONTS = [
  ('OTF/ipag.ttf', 'IPAGothic'),
  ('OTF/ipamp.ttf', 'IPAPMincho'),
  ('TTF/togoshi-gothic.ttf', 'TogoshiGothic'),
  ('TTF/togoshi-mincho.ttf', 'TogoshiMincho'),
  ('TTF/togoshi-monago.ttf', 'TogoshiMonago'),
  ('TTF/togoshi-mono.ttf', 'TogoshiMono'),
  ('TTF/umeplus-gothic.ttf', 'UmeplusGothic'),
  ('TTF/kiloji.ttf', 'Kiloji'),
  # NOTE: the below seem to render wrong for some or all content
  # ('TTF/dejima-mincho.ttf', 'DejimaMincho'),
  # ('TTF/sazanami-gothic.ttf', 'SazanamiGothic'),
  # ('TTF/sazanami-mincho.ttf', 'SazanamiMincho'),
  # ('TTF/DroidSansJapanese.ttf', 'DroidSansJapanese'),
]

MARGIN=8
FONT_SIZE=18


imagefont_cache = {}
glyph_cache = {}


def mkdirs_silent(path):
  try:
    makedirs(path)
  except Exception, e:
    pass


def make_boxes(font_path, lines, margin=MARGIN):
  boxes = []
  x = margin
  y = margin
  for line in lines:
    line_height = 0
    for c in line:
      width, height = imagefont_cache[font_path].getsize(c)
      line_height = max(height, line_height)
      # only draw and box character if the glyph is in the font
      if ord(c) in glyph_cache[font_path] and not c in ' ':
        boxes.append(
            (c, x, y, (x + width), (y + height))
            )
      x += width + margin
    x = margin
    y += line_height + margin

  return boxes


def write_boxes(dirpath, lang, font_name, exp, boxes):
  image_width, image_height = calculate_image_size(
      boxes,
      margin=MARGIN)
  if boxes:
    box_dir = path.join('train', dirpath)
    box_filename = '{}.{}.exp{}.box'.format(lang, font_name, exp)
    mkdirs_silent(box_dir)
    with open(path.join(box_dir, box_filename), 'w+') as box_file:
      for c, x, y, x2, y2 in boxes:
        box_file.write(
            '{} {} {} {} {} 0\n'.format(
                c.encode('utf-8'),
                x,
                image_height - y2,
                x2,
                image_height - y,
                )
            )


def calculate_image_size(boxes, margin=MARGIN):
  image_width = 0
  image_height = 0

  for (c, x, y, x2, y2) in boxes:
    image_width = max(image_width, x2)
    image_height = max(image_height, y2)

  return (image_width + margin, image_height + margin)


def draw_text_wand(dirpath, lang, font_name, exp, font_path, boxes, margin=MARGIN):
  image_width, image_height = calculate_image_size(
      boxes,
      margin=MARGIN)
  img_dir = path.join('train', dirpath)
  img_filename = '{}.{}.exp{}.{}'.format(lang, font_name, exp, IMAGE_EXT)
  mkdirs_silent(img_dir)
  img_path = path.join(img_dir, img_filename)
  with wand.color.Color('white') as bg:
    with wand.drawing.Drawing() as draw:
      with wand.image.Image(
          width=image_width,
          height=image_height,
          background=bg,
          ) as image:
        draw.font = font_path
        draw.font_size = FONT_SIZE
        for (c, x, y, x2, y2) in boxes:
          draw.text(x, (y + (FONT_SIZE - MARGIN), c.encode('utf-8'))
        draw(image)
        # print(img_path)
        image.save(filename=img_path)


def draw_text_pil(dirpath, lang, font_name, exp, font_path, boxes, margin=MARGIN):
  image_width, image_height = calculate_image_size(
      boxes,
      margin=MARGIN)
  img = Image.new(
      "RGBA",
      (image_width, image_height),
      (255, 255, 255),
      )
  draw = ImageDraw.Draw(img)

  draw.setfont(imagefont_cache[font_path])

  for (c, x, y, x2, y2) in boxes:
    draw.text((x, y), c, (0, 0, 0))

  img_dir = path.join('train', dirpath)
  img_filename = '{}.{}.exp{}.{}'.format(lang, font_name, exp, IMAGE_EXT)
  mkdirs_silent(img_dir)
  img.save(path.join(img_dir, img_filename))

  # PIL leaks memory like a ...
  draw.setfont(None)
  img.resize((0, 0))

  del draw
  del img


def parse_args():
  parser = argparse.ArgumentParser(
      description='Generate image/box pair training set from documents',
      )
  parser.add_argument(
      '--lines',
      metavar='l',
      type=int,
      default=10,
      help='lines per image file',
      )
  return parser.parse_args()


if __name__ == '__main__':
  args = parse_args()
  n_lines = args.lines

  for font_file, font_name in FONTS:
    font_path = FONT_DIR + font_file
    imagefont_cache[font_path] = ImageFont.truetype(font_path, FONT_SIZE)
    glyph_cache[font_path] = {
        glyph.unicode: glyph
        for glyph in fontforge.open(font_path).glyphs()
        }

  i = 0
  for (dirpath, dirnames, filenames) in walk(DOCS_DIR):
    for filename in filenames:
      with open(path.join(dirpath, filename)) as text_file:
        text_content = text_file.read().decode('utf-8')
        all_lines = text_content.splitlines()
        for j in range(0, len(all_lines), n_lines):
          lines = all_lines[j:(j + n_lines)]
          if lines:
            for font_file, font_name in FONTS:
              font_path = FONT_DIR + font_file
              lang='jpn'
              exp=i
              boxes = make_boxes(font_path, lines, margin=MARGIN)
              write_boxes(dirpath, lang, font_name, exp, boxes)

              # draw_text_pil(dirpath, lang, font_name, exp, font_path, boxes)
              draw_text_wand(dirpath, lang, font_name, exp, font_path, boxes)
            i += 1
