#!/usr/bin/env python
# coding: UTF-8


from os import walk, path, environ
import argparse


def cat(docs, lang, fonts, output_file='{}.meta.box'):
  with open(output_file.format(lang), 'w+') as meta_file:
    for (dirpath, dirnames, filenames) in walk(docs):
      print(dirpath)
      for filename in filenames:
        if filename.endswith('box'):
          with open(path.join(dirpath, filename)) as text_file:
            meta_file.write(text_file.read())


def parse_args():
  parser = argparse.ArgumentParser(
      description='cat all box files',
      )
  parser.add_argument(
      '--docs',
      metavar='d',
      type=str,
      default='train',
      )
  parser.add_argument(
      '--lang',
      metavar='l',
      type=str,
      default='jpn',
      )
  parser.add_argument(
      'font_name',
      type=str,
      nargs='+',
      help='font names',
      )
  parser.add_argument(
      '--output',
      metavar='o',
      type=str,
      default='{}.meta.box',
      nargs='?',
      )
  return parser.parse_args()


if __name__ == '__main__':
  args = parse_args()
  cat(
      docs=args.docs,
      lang=args.lang,
      fonts=args.font_name,
      output_file=args.output,
      )