# -*- coding: utf-8 -*-
"""
Document management system
==========================

This extension is a basic implementation of DMS_. It features:

* a command-line interface for adding scanned papers (including batch
  processing with OCR_ and custom metadata);
* web interface for search and retrieval (with thumbnails and OCR_ results).

The extension aims to provide the following capabilities:

* *Metadata*:

  * summary (entered manually or automatically fetched from filename);
  * date and time of storage;
  * source file fingerprint (so the same file will not be imported twice).

* *Integration*: the data is stored in a document-oriented database within the
  OrgTool ecosystem, so it is pretty easy to reference the scanned papers from
  other types of documents or even merge them.
* *Capture*: the system allows batch import of scanned papers (images) with OCR_
  processing on the fly. Direct scanning is also supported.
* *Indexing*: see "Searching" and "Retrieval" below. Pages are organized in
  "papers" (one or more pages) and pages can be organized by topic or linked to
  other objects.
* *Storage*: the scanned papers (images) are bound to database records
  (documents) and stored in the file system. The application manages the
  coupling.
* *Retrieval*: currently rather simple: by key, full-text search, categorization.
  See also: `document retrieval`_.
* *Distribution*: *not yet* (see "Publishing" below).
* *Security*: its up to you. No need to store private data anywhere outside of
  your PC (unless you need to).
* *Workflow*: *not yet* (and unsure if it belongs to this library at all).
* *Collaboration*: *not yet* (this is rather a home system as of now).
* *Versioning*: *not yet*.
* *Searching*: the documents can be searched by summary or by details. Note that
  details are usually extracted automatically from the image via OCR_.
* *Publishing*: *not yet*. Export to PDF may be added later (with pages
  automatically glued into a single document).
* *Reproduction*: the images are stored as is and can be printed out.

.. _DMS: http://en.wikipedia.org/wiki/Document_management_system
.. _OCR: http://en.wikipedia.org/wiki/Optical_character_recognition
.. _document retrieval: http://en.wikipedia.org/wiki/Document_retrieval

API reference
-------------
"""
from tool.plugins import BasePlugin
from tool.ext.templating import register_templates

from commands import add_pages, ocr


class PapersCLI(BasePlugin):
    """Storage for scanned documents with integrated OCR support.

    Example configuration (YAML)::

        devel_papers.Papers:
            # this is where the files will be actually stored
            # (do not add/rename/move/delete them there manually!):
            image_base_path: /home/johndoe/images/scanned_papers/

    .. note::

        This extension uses CuneiForm for optical character recignition. It is
        optional but should be installed in order to enable OCR.

    """
    features = 'papers'
    requires = ['{document_storage}']
    commands = [add_pages, ocr]

    def make_env(self, image_base_path):
        return {'image_base_path': image_base_path}


class PapersWeb(PapersCLI):
    requires = PapersCLI.requires + ['{routing}', '{templating}']

    def make_env(self, **kw):
        register_templates(__name__)
        return super(PapersWeb, self).make_env(**kw)
