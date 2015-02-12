#!/usr/bin/env python
# vim: set fileencoding=utf-8

import argparse

from ofxtools.Parser import OFXTree

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')

    args = parser.parse_args()

    parser = OFXTree()
    for f in args.files:
        print("Parsing %s" % f)
        parser.parse(f) 
        parser.convert(strict=False)
