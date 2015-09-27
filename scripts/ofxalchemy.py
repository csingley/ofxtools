#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

import argparse
import sys

from sqlalchemy import create_engine

from ofxtools.ofxalchemy import Base, DBSession, OFXParser


def log(message, end='\n'):
    print(message, end=end)
    sys.stdout.flush()


if __name__ == '__main__':
    # CLI arg handling
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--output', default='sqlite:///test.db',
                        help='Destination database URI')
    args = parser.parse_args()

    # DB setup
    engine = create_engine(args.output, echo=args.verbose)
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    parser = OFXParser()
    for filename in args.files:
        log('Parsing "{}"...'.format(filename), end='')
        parser.parse(filename)
        log('done. Commiting to database...', end='')
        parser.instantiate()
        DBSession.commit()
        log('done!')
