#
# Configuration file for the Sphinx documentation builder.
#
# http://www.sphinx-doc.org/en/master/config

from importlib.metadata import metadata

_meta = metadata("ofxtools")

# -- Project information -----------------------------------------------------
project = _meta["Name"]
author = _meta["Author-email"].split("<")[0].strip()
copyright = f"2010–2026 {author}"
version = release = _meta["Version"]


# -- General configuration ---------------------------------------------------

extensions = []
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = None


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# -- Options for HTMLHelp output ---------------------------------------------

htmlhelp_basename = "ofxtoolsdoc"


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {}
latex_documents = [
    (
        master_doc,
        "ofxtools.tex",
        "ofxtools Documentation",
        author,
        "manual",
    )
]


# -- Options for manual page output ------------------------------------------

man_pages = [(master_doc, "ofxtools", "ofxtools Documentation", [author], 1)]


# -- Options for Texinfo output ----------------------------------------------

texinfo_documents = [
    (
        master_doc,
        "ofxtools",
        "ofxtools Documentation",
        author,
        "ofxtools",
        "Library for working with Open Financial Exchange (OFX) data",
        "Miscellaneous",
    )
]


# -- Options for Epub output -------------------------------------------------

epub_title = project
epub_exclude_files = ["search.html"]
