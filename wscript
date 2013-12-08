#!/usr/bin/env python
# coding: UTF-8


import os

from waflib import TaskGen
from waflib.Task import Task


### waf tools

# TaskGen.declare_chain(
#     name='touchtr',
#     rule = 'touch ${TGT}',
#     ext_in = ['.png', '.jpg', 'jpeg', '.tif', '.tiff'],
#     # ext_out = '.tr',
#     shell = False,
#     reentrant = True,
#     )

# TaskGen.declare_chain(
#     rule = '${TESSERACT} ${SRC} ${TGT[0].bld_base()} box.train.stderr',
#     ext_in = ['.png', '.jpg', 'jpeg', '.tif', '.tiff'],
#     ext_out = '.tr',
#     shell = False,
#     # reentrant = False,
#     )

# TaskGen.declare_chain(
#     rule = (
#         '${TESSERACT} "${SRC}" "${SRC[0].get_bld().bld_base()}" box.train.stderr ' +
#             # HACK: force waf to create folder hierarchy
#             ' #${SRC[0].get_bld().parent.mkdir()}'
#         ),
#     ext_in = ['.png', '.jpg', 'jpeg', '.tif', '.tiff'],
#     # NOTE: no targets are set since tesseract might fail with: "Empty page!!"
#     shell = True,
#     )

def box_scanner(task):
  node = task.inputs[0]
  # node.get_bld().parent.mkdir()
  dep = node.parent.find_resource(node.name.replace('.png', '.box'))
  if not dep:
    raise ValueError("Could not find the .box file for %r" % node)
  return ([dep], [])

TaskGen.declare_chain(
    name='trs',
    rule = '${TESSERACT} ${SRC} ${TGT[0].bld_base()} box.train.stderr',
    ext_in = ['.png', '.jpg', 'jpeg', '.tif', '.tiff'],
    ext_out = ['.tr'],
    scan = box_scanner,
    )


### build script

def options(ctx):
  pass


def configure(ctx):
  ctx.find_program('mv', var='MOVE')
  ctx.find_program('cp', var='COPY')
  ctx.find_program('cat', var='CAT')
  ctx.find_program('tesseract', var='TESSERACT')
  ctx.find_program('combine_tessdata', var='COMBINE_TESSERACT')
  ctx.find_program('unicharset_extractor', var='UNICHARSET_EXTRACTOR')
  ctx.find_program('mftraining', var='MFTRAINING')
  ctx.find_program('cntraining', var='CNTRAINING')
  ctx.find_program(
      'meta_box.py',
      var='META_BOX',
      path_list=[ctx.path.abspath()],
      )
  #
  ctx.env.MODEL_LANG = 'jpn'
  ctx.env.IMAGE_EXT = 'png'
  ctx.env.EXP_FONTS = [
    'IPAGothic',
    'IPAPMincho',
    'TogoshiGothic',
    'TogoshiMincho',
    'TogoshiMonago',
    'TogoshiMono',
    'UmeplusGothic',
    'Kiloji',
  ]


def build(ctx):
  copy_in_config(ctx)

  cat_meta_box(ctx)
  extract_unicharset(ctx)

  for font in ctx.env.EXP_FONTS:
    image_glob = 'train/documents/*/{}.{}.exp*.{}'.format(
        ctx.env.MODEL_LANG,
        font,
        ctx.env.IMAGE_EXT,
        )
    ctx(source=ctx.path.ant_glob(image_glob))
  cat_per_font_trs(ctx)

  train_mf(ctx)

  train_cn(ctx)

  make_normproto_lang_specific(ctx)
  make_inttemp_lang_specific(ctx)
  make_pffmtable_lang_specific(ctx)

  combine(ctx)


def copy_in_config(ctx):
  lang = ctx.env.MODEL_LANG
  ctx(
      rule='${COPY} ${SRC} ${TGT}',
      source=ctx.path.make_node(
          'tessdata/{}.config'.format(lang)
          ),
      target=ctx.path.get_bld().make_node(
          '{}.config'.format(lang)
          ),
      )
  ctx(
      rule='${COPY} ${SRC} ${TGT}',
      source=ctx.path.make_node(
          'tessdata/{}.font_properties'.format(lang)
          ),
      target=ctx.path.get_bld().make_node(
          '{}.font_properties'.format(lang)
          ),
      )
  ctx(
      rule='${COPY} ${SRC} ${TGT}',
      source=ctx.path.make_node(
          'tessdata/{}.punc-wordlist'.format(lang)
          ),
      target=ctx.path.get_bld().make_node(
          '{}.punc-wordlist'.format(lang)
          ),
      )
  ctx(
      rule='${COPY} ${SRC} ${TGT}',
      source=ctx.path.make_node(
          'tessdata/{}.unicharambigs'.format(lang)
          ),
      target=ctx.path.get_bld().make_node(
          '{}.unicharambigs'.format(lang)
          ),
      )


""" From: https://code.google.com/p/tesseract-ocr/wiki/TrainingTesseract3
An alternative to multi-page tiffs is to create many single-page tiffs
for a single font, and then you must cat together the tr files for each font
into several single-font tr files.
In any case, the input tr files to mftraining must each contain
a single font.
"""
def cat_per_font_trs(ctx):
  for font in ctx.env.EXP_FONTS:
    tr_glob = 'train/documents/*/{}.{}.exp*.tr'.format(
        ctx.env.MODEL_LANG,
        font,
        )
    ctx(
        rule='${{CAT}} {} > ${{TGT}}'.format(tr_glob),
        source=ctx.path.ant_glob(tr_glob),
        target=ctx.path.get_bld().make_node(
            'train/{}.{}.exp.tr'.format(ctx.env.MODEL_LANG, font)
            ),
        after=['trs'],
        )


def cat_meta_box(ctx):
  boxes = []
  for font in ctx.env.EXP_FONTS:
    box_glob = 'train/documents/*/{}.{}.exp*.box'.format(
        ctx.env.MODEL_LANG,
        font,
        )
    boxes.extend(ctx.path.ant_glob(box_glob))
  ctx(
      rule=(
          '${META_BOX}' +
              '--docs ${bld.path.find_dir("train").abspath()}' +
              '--lang ${MODEL_LANG}' +
              '--output ${TGT}' +
              '${EXP_FONTS}'
          ),
      source=boxes,
      target=ctx.path.get_bld().make_node(
          '{}.meta.box'.format(ctx.env.MODEL_LANG)
          ),
      shell=False,
      )

# unicharset_extractor lang.font.exp0.box [lang.font.exp1.box ...]
def extract_unicharset(ctx):
  ctx(
      rule='${UNICHARSET_EXTRACTOR} ${SRC}',
      source='{}.meta.box'.format(ctx.env.MODEL_LANG),
      target='unicharset',
      )


# shapeclustering -F lang.font_properties -U unicharset lang.font.exp0.tr [...]
def create_shapetable(ctx):
  # NOTE: shapetable shouldn't be used except for Indic languages
  pass


# mftraining -F lang.font_properties -U unicharset -O lang.unicharset *.tr
def train_mf(ctx):
  trs = []
  for font in ctx.env.EXP_FONTS:
    trs.append('train/{}.{}.exp.tr'.format(ctx.env.MODEL_LANG, font))
  ctx(
      rule=(
          '${MFTRAINING}' +
              ' -F ${SRC[0].bldpath()}' +
              ' -U ${SRC[1].bldpath()}' +
              ' -O ${TGT[0].bldpath()}' +
              ' {}'.format(' '.join(trs))
              # ' {}'.format(' '.join([tr.bldpath() for tr in trs]))
              # ' ${SRC[2:]}'
            ),
      source=[
          'tessdata/{}.font_properties'.format(ctx.env.MODEL_LANG),
          'unicharset',
          ] + trs,
      target=[
          '{}.unicharset'.format(ctx.env.MODEL_LANG),
          'inttemp',
          'pffmtable',
          ]
      )


# cntraining lang.fontname.exp0.tr [lang.fontname.exp1.tr ...]
def train_cn(ctx):
  trs = []
  for font in ctx.env.EXP_FONTS:
    trs.append('train/{}.{}.exp.tr'.format(ctx.env.MODEL_LANG, font))
  ctx(
      rule='${CNTRAINING} ${SRC}',
      source=trs,
      target=ctx.path.get_bld().make_node(
          'normproto'
          ),
      )


def make_normproto_lang_specific(ctx):
  ctx(
      rule='${MOVE} ${SRC} ${TGT}',
      source=ctx.path.get_bld().make_node(
          'normproto'
          ),
      target=ctx.path.get_bld().make_node(
          '{}.normproto'.format(ctx.env.MODEL_LANG)
          ),
      )

def make_inttemp_lang_specific(ctx):
  ctx(
      rule='${MOVE} ${SRC} ${TGT}',
      source=ctx.path.get_bld().make_node(
          'inttemp'
          ),
      target=ctx.path.get_bld().make_node(
          '{}.inttemp'.format(ctx.env.MODEL_LANG)
          ),
      )

def make_pffmtable_lang_specific(ctx):
  ctx(
      rule='${MOVE} ${SRC} ${TGT}',
      source=ctx.path.get_bld().make_node(
          'pffmtable'
          ),
      target=ctx.path.get_bld().make_node(
          '{}.pffmtable'.format(ctx.env.MODEL_LANG)
          ),
      )


def combine(ctx):
  lang = ctx.env.MODEL_LANG
  ctx(
      rule='${COMBINE_TESSERACT} ${MODEL_LANG}.',
      source=[
        ctx.path.get_bld().make_node('{}.config'.format(lang)),
        '{}.font_properties'.format(lang),
        '{}.punc-wordlist'.format(lang),
        '{}.unicharambigs'.format(lang),
        '{}.normproto'.format(lang),
        '{}.inttemp'.format(lang),
        '{}.pffmtable'.format(lang),
      ]
      )
