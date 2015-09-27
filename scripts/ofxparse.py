#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

import argparse
import sys

from ofxtools.Parser import OFXTree


def log(message, end='\n'):
    print(message, end=end)
    sys.stdout.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    parser = OFXTree()
    for filename in args.files:
        log('Parsing "{}"...'.format(filename), end='')
        parser.parse(filename)
        parser.convert()
        log('done!')
