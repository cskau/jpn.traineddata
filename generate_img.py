#!/usr/bin/env python2
# coding: UTF-8


from os import walk, path, makedirs

import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

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

MARGIN=4


def mkdirs_silent(path):
  try:
    makedirs(path)
  except Exception, e:
    pass

def draw_text(dirpath, lang, font_name, exp, font_file, txt, margin=MARGIN):
  font = ImageFont.truetype(FONT_DIR + font_file, 18)
  ff = fontforge.open(FONT_DIR + font_file)

  font_glyphs = {glyph.unicode: glyph for glyph in ff.glyphs()}

  lines = txt.split('\n')

  image_width = 0
  image_height = 0
  for line in lines:
    width, height = font.getsize(line)
    width += ((len(line) - 1) * margin)
    image_width = max(width, image_width)
    image_height += height + margin

  image_width += 2 * margin
  image_height += margin

  img = Image.new(
      "RGBA",
      (image_width, image_height),
      (255, 255, 255),
      )
  draw = ImageDraw.Draw(img)

  boxes = []
  x = margin
  y = margin
  for line in lines:
    line_height = 0
    for c in line:
      width, height = font.getsize(c)
      line_height = max(height, line_height)
      # only draw and box character if the glyph is in the font
      if ord(c) in font_glyphs:
        draw.text(
            (x, y),
            c,
            (0, 0, 0),
            font=font,
            )
        boxes.append(
            (c, x, y, (x + width), (y + height))
            )
      x += width + margin
    x = margin
    y += line_height + margin

  img_dir = path.join('train', dirpath)
  img_filename = '{}.{}.exp{}.{}'.format(lang, font_name, exp, IMAGE_EXT)
  mkdirs_silent(img_dir)
  img.save(path.join(img_dir, img_filename))

  if boxes:
    box_dir = path.join('train', dirpath)
    box_filename = '{}.{}.exp{}.box'.format(lang, font_name, exp)
    mkdirs_silent(box_dir)
    with open(path.join(box_dir, box_filename), 'w+') as box_file:
      for c, x, y, x2, y2 in boxes:
        box_file.write(
            '{} {} {} {} {} 0\n'.format(c.encode('utf-8'), x, y, x2, y2)
            )


if __name__ == '__main__':
  i = 0
  texts = []
  for (dirpath, dirnames, filenames) in walk(DOCS_DIR):
    for filename in filenames:
      with open(path.join(dirpath, filename)) as text_file:
        text_content = text_file.read().decode('utf-8')
        for line in text_content.splitlines():
          if line:
            for font_file, font_name in FONTS:
              draw_text(dirpath, 'jpn', font_name, i, font_file, line)
            i += 1
