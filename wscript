#!/usr/bin/env python
# coding: UTF-8

import os


def options(ctx):
  pass


def configure(ctx):
  ctx.env.TESSERACT = 'tesseract'
  ctx.env.COMBINE_TESSERACT = 'combine_tessdata'
  ctx.env.UNICHARSET_EXTRACTOR = 'unicharset_extractor'
  ctx.env.MFTRAINING = 'mftraining'
  ctx.env.CNTRAINING = 'cntraining'
  #
  ctx.env.MODEL_LANG = 'jpn'
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
  extract_unicharset(ctx)
  cat_per_font_trs(ctx)
  train_box(ctx)
  train_mf(ctx)
  train_cn(ctx)
  make_normproto_lang_specific(ctx)
  make_inttemp_lang_specific(ctx)
  make_pffmtable_lang_specific(ctx)
  combine(ctx)
  test(ctx)


def train_box(ctx):
  for font in ctx.env.EXP_FONTS:
    image_glob = 'train/{}.{}.exp*.png'.format(ctx.env.MODEL_LANG, font)
    images = ctx.path.ant_glob(image_glob)
    for image in images:
      # TODO: we should check if the .box files exist too
      image_path = image.bldpath()
      exp_path = '.'.join(image_path.split('.')[:-1])
      tr_path = '{}.tr'.format(exp_path)
      rule = '${{TESSERACT}} ${{SRC}} {} box.train.stderr'.format(exp_path)
      ctx(
          rule=rule,
          source=image_path,
          target=tr_path,
          )


""" From: https://code.google.com/p/tesseract-ocr/wiki/TrainingTesseract3
An alternative to multi-page tiffs is to create many single-page tiffs
for a single font, and then you must cat together the tr files for each font
into several single-font tr files.
In any case, the input tr files to mftraining must each contain
a single font.
"""
def cat_per_font_trs(ctx):
  trs = []
  for font in ctx.env.EXP_FONTS:
    # TODO: use terminal glob directly in rule? (don't use source)
    tr_glob = 'train/{}.{}.exp*.tr'.format(ctx.env.MODEL_LANG, font)
    ctx(
        rule='cat ${SRC} > ${TGT}',
        source=ctx.path.ant_glob(tr_glob),
        target='train/{}.{}.exp.tr'.format(ctx.env.MODEL_LANG, font)
        )


# unicharset_extractor lang.font.exp0.box [lang.font.exp1.box ...]
def extract_unicharset(ctx):
  boxes = []
  for font in ctx.env.EXP_FONTS:
    box_glob = 'train/{}.{}.exp*.box'.format(ctx.env.MODEL_LANG, font)
    boxes.extend(ctx.path.ant_glob(box_glob))
  # TODO: we probably need to create a meta-box file since with large
  #  training sets the command line would be /very/ long
  ctx(
      rule='${UNICHARSET_EXTRACTOR} ${SRC}',
      source=boxes,
      target='unicharset'
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
              ' -F ${SRC[0]}' +
              ' -U ${SRC[1]}' +
              ' -O ${TGT[0]}' +
              ' {}'.format(' '.join(trs))
              # ' {}'.format(' '.join([tr.bldpath() for tr in trs]))
              # ' ${SRC[2:]}'
            ),
      source=[
          '{}.font_properties'.format(ctx.env.MODEL_LANG),
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
      target='normproto',
      )


def make_normproto_lang_specific(ctx):
  ctx(
      rule='mv ${SRC} ${TGT}',
      source='normproto',
      target='{}.normproto'.format(ctx.env.MODEL_LANG),
      )

def make_inttemp_lang_specific(ctx):
  ctx(
      rule='mv ${SRC} ${TGT}',
      source='inttemp',
      target='{}.inttemp'.format(ctx.env.MODEL_LANG),
      )

def make_pffmtable_lang_specific(ctx):
  ctx(
      rule='mv ${SRC} ${TGT}',
      source='pffmtable',
      target='{}.pffmtable'.format(ctx.env.MODEL_LANG),
      )


def copy_in_config(ctx):
  ctx(
      rule='cp ${SRC} ${TGT}',
      source='tessdata/jpn.config',
      target='jpn.config',
      )
  ctx(
      rule='cp ${SRC} ${TGT}',
      source='tessdata/jpn.font_properties',
      target='jpn.font_properties',
      )
  ctx(
      rule='cp ${SRC} ${TGT}',
      source='tessdata/jpn.punc-wordlist',
      target='jpn.punc-wordlist',
      )
  ctx(
      rule='cp ${SRC} ${TGT}',
      source='tessdata/jpn.unicharambigs',
      target='jpn.unicharambigs',
      )


def combine(ctx):
  lang = ctx.env.MODEL_LANG
  ctx(
      rule='${COMBINE_TESSERACT} ${MODEL_LANG}.',
      source=[
        '{}.config'.format(lang),
        '{}.font_properties'.format(lang),
        '{}.punc-wordlist'.format(lang),
        '{}.unicharambigs'.format(lang),
        '{}.normproto'.format(lang),
        '{}.inttemp'.format(lang),
        '{}.pffmtable'.format(lang),
      ]
      )
