#!/usr/bin/env python
# coding: UTF-8

import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw


FONT_DIR='/usr/share/fonts/OTF/'


def draw_text(lang, font_name, font_file, txt, margin=10):
  boxes = []

  font = ImageFont.truetype(FONT_DIR + font_file, 18)

  image_width = 0
  image_height = 0
  for line in txt.split('\n'):
    width, height = font.getsize(line)
    width += ((len(line) - 1) * margin)
    image_width = max(width, image_width)
    image_height += height

  image_width += 2 * margin
  image_height += 2 * margin

  img = Image.new(
      "RGBA",
      (image_width, image_height),
      (255, 255, 255),
      )
  draw = ImageDraw.Draw(img)

  x = margin
  y = margin
  for line in txt.split('\n'):
    for c in line:
      width, height = font.getsize(c)
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
    y += height + margin

  img.save('{}.{}.exp0.tiff'.format(lang, font_name))

  with open('{}.{}.exp0.box'.format(lang, font_name), 'w+') as box_file:
    for c, x, y, x2, y2 in boxes:
      box_file.write(
          '{} {} {} {} {} 0\n'.format(c, x, y, x2, y2)
          )


if __name__ == '__main__':
  boxes = draw_text(
      'jpn',
      'IPAGothic',
      'ipag.ttf',
      '野島は自分で云っている内に、なんだかわけがわからなくなった。',
      )
  'UmePlusPGothic'