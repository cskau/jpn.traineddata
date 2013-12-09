#!/usr/bin/env python
# coding: UTF-8


from os import walk, path, environ
import subprocess
import argparse

import numpy


TEST_DIR='test'


def word_error_rate(substitutions, insertions, deletions, n):
  return (substitutions + insertions + deletions) / n


def backtrack(matrix):
  i, j = (lambda wh: (wh[0]-1, wh[1]-1))(matrix.shape)
  wer = matrix[i][j]
  substitutions, insertions, deletions = 0, 0, 0
  while i > 0 or j > 0:
    if i > 0 and j > 0 and matrix[i-1][j-1] < matrix[i][j]:
      i -= 1
      j -= 1
      substitutions += 1
    elif j > 0 and matrix[i][j-1] < matrix[i][j]:
      j -= 1
      insertions += 1
    elif i > 0 and matrix[i-1][j] < matrix[i][j]:
      i -= 1
      deletions += 1
    else:
      i -= 1
      j -= 1

  return (substitutions, insertions, deletions)


def create_word_matrix(ground_truth, estimate):
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

  return matrix


def run_tesseract(image_path, lang='jpn', prefix='build/'):
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


def run_all_tests(lang, prefix):
  test_results = []
  for (dirpath, dirnames, filenames) in walk(TEST_DIR):
    for filename in filenames:
      if filename.endswith('txt'):
        file_path = path.join(dirpath, filename)
        image_path = '{}png'.format(file_path[:-3])
        ocr_path = '{}png.ocr.txt'.format(file_path[:-3])
        if path.exists(image_path):
          print(image_path)
          stdout, stderr = run_tesseract(image_path, lang, prefix)
          if stderr: # TODO
            print(stderr.decode())
            # exit(1)
          text_content = ''
          with open(file_path) as text_file:
            text_content = text_file.read()
          ocr_content = ''
          with open(ocr_path) as text_file:
            ocr_content = text_file.read()
          test_results.append((image_path, text_content, ocr_content))
  return test_results


def get_pair_numbers(pairs):
  pair_numbers = []
  for label, expected, actual in pairs:
    word_matrix = create_word_matrix(expected, actual)
    s, i, d = backtrack(word_matrix)
    pair_numbers.append((label, s, i, d, word_matrix.shape[0]))
  return pair_numbers


def print_werewolves(pair_numbers):
  print('   WER    Sub    Ins    Del  File')
  S, I, D, N = 0, 0, 0, 0
  for label, s, i, d, n in pair_numbers:
    print('{:6.2f}  {:>5}  {:>5}  {:>5}  {:<}'.format(
        word_error_rate(s, i, d, n), s, i, d, label))
    S += s
    I += i
    D += d
    N += n
  print('==============================================')
  print('{:6.2f}  {:>5}  {:>5}  {:>5}'.format(
      word_error_rate(S, I, D, N), S, I, D))


def parse_args():
  parser = argparse.ArgumentParser(
      description='Run model on test set in the ./test/ folder',
      )
  parser.add_argument(
      '--lang',
      metavar='l',
      type=str,
      nargs='?',
      default='jpn',
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
  test_results = run_all_tests(
      lang=args.lang,
      prefix=args.prefix if not args.builtin else None,
      )
  pair_numbers = get_pair_numbers(test_results)
  print_werewolves(pair_numbers)