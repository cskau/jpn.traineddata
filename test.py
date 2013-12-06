#!/usr/bin/env python
# coding: UTF-8


from os import walk, path, environ
import subprocess
import argparse

import numpy


TEST_DIR='test'


def word_error_rate(ground_truth, estimate):
  w = len(ground_truth)
  h = len(estimate)
  matrix = numpy.zeros(((w+1), (h+1)), dtype=numpy.uint16)
  for i in range(w+1):
    for j in range(h+1):
      if i == 0:
        matrix[0][j] = j
      elif j == 0:
        matrix[i][0] = i
      elif ground_truth[i-1] == estimate[j-1]:
        matrix[i][j] = matrix[i-1][j-1]
      else:
        matrix[i][j] = 1 + min(
            matrix[i-1][j-1], # substitution
            matrix[i][j-1], # insertion
            matrix[i-1][j], # deletion
            )

  return matrix[w][h]


def run_tesseract(image_path, lang=path.join('..', 'jpn'), prefix='build/'):
  env = environ.copy()
  if prefix:
    env['TESSDATA_PREFIX'] = prefix
  stdout, stderr = subprocess.Popen(
      [
        'tesseract',
        '-l',
        lang,
        image_path,
        '{}.ocr'.format(image_path),
      ],
      env=env,
      # cwd=
      # stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      ).communicate()
  return stdout, stderr


def test(lang, prefix):
  wer_acc = 0
  for (dirpath, dirnames, filenames) in walk(TEST_DIR):
    for filename in filenames:
      if filename.endswith('txt'):
        file_path = path.join(dirpath, filename)
        image_path = '{}png'.format(file_path[:-3])
        ocr_path = '{}png.ocr.txt'.format(file_path[:-3])
        if path.exists(image_path):
          stdout, stderr = run_tesseract(image_path, lang, prefix)
          # if stderr:
          #   print(stderr.decode())
          #   exit(1)
          text_content = ''
          with open(file_path) as text_file:
            text_content = text_file.read()
          ocr_content = ''
          with open(ocr_path) as text_file:
            ocr_content = text_file.read()
          wer = word_error_rate(text_content, ocr_content)
          wer_acc += wer
          print('{:>4} : {}'.format(wer, image_path))
  # summary
  print('==========='.format(wer_acc))
  print('{:>4}'.format(wer_acc))


def parse_args():
  parser = argparse.ArgumentParser(
      description='Run model on test set in the ./test/ folder',
      )
  parser.add_argument(
      '--lang',
      metavar='l',
      type=str,
      nargs='?',
      default='../jpn',
      help='lang.traineddata',
      )
  parser.add_argument(
      '--prefix',
      metavar='p',
      type=str,
      nargs='?',
      default='build/',
      help='TESSDATA_PREFIX',
      )
  parser.add_argument(
      '--builtin',
      action='store_true',
      help='Use installed tessdata',
      )
  return parser.parse_args()


if __name__ == '__main__':
  args = parse_args()
  test(
      lang=args.lang if not args.builtin else 'jpn',
      prefix=args.prefix if not args.builtin else None,
      )