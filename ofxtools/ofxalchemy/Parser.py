# vim: set fileencoding=utf-8
""" 
Version of ofxtools.Parser that uses SQLAlchemy for conversion
"""
# local imports
import ofxtools
from ofxtools.ofxalchemy import Response 

OFXTree = ofxtools.Parser.OFXTree
OFXTree.ofxresponse = Response.OFXResponse

