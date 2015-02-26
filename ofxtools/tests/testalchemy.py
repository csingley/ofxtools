#!/usr/bin/env python
# vim: set fileencoding=utf-8

# stdlib imports
import argparse

# 3rd party libraries
from sqlalchemy import create_engine

# local imports
from ofxtools.ofxalchemy import (
    DBSession,
    Base,
    OFXParser,
    )


if __name__ == "__main__":
    # CLI arg handling
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('-v', '--verbose', action='store_true') 

    args = parser.parse_args()

    # DB setup
    engine = create_engine('sqlite:///test.db', echo=args.verbose)
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    
    parser = OFXParser()
    for f in args.files:
        print("Parsing %s" % f)
        parser.parse(f) 
        parser.instantiate()
        DBSession.commit()

