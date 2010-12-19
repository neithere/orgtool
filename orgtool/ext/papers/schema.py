# -*- coding: utf-8 -*-

from doqu import Document, Many
from doqu.fields import *
from orgtool.ext.tracking.schema import TrackedDocument


def get_image_base_path():
    from tool import app
    ext = app.get_feature('papers')
    return ext.env['image_base_path']


class Page(TrackedDocument):
    summary = Field(unicode, required=True)
    details = Field(unicode)
    image = ImageField(get_image_base_path, required=True)
    language = Field(unicode)  # "en", "cze", etc. — mainly for OCR (CuneiForm)
    source_fingerprint = Field(str)  # ETL: not necessarily current file

    def __unicode__(self):
        return u'{summary}'.format(**self)

    def save(self, *args, **kwargs):
        #self['image'].save()
        #self['file_hash'] = self.get_file_hash()
        #self['details'] = image_to_text(path=self['image'].full_path,
        #                                language=self['language'])
        return super(Page, self).save(*args, **kwargs)

    def get_image_url(self):
        # FIXME
        return u'/media/scanned_papers/{0}'.format(self.image.path)


class Paper(TrackedDocument):
    summary = Field(unicode, required=True)
    details = Field(unicode)
    pages = Many(Page)


### OCR stuff
'''
# TODO: refactor this away and maybe make an abstraction layer for OCRs
# see also: https://github.com/hoffstaetter/python-tesseract
OUT_FILENAME = __name__+'auto-cuneiform.txt'
def image_to_text(path, language='eng'):
    """Parses image using an OCR utility and returns resulting plain text.

    :param path: path to file (string)
    :param language: language name (e.g. "English" or "eng" but *not* "en")

    Usage::

        text = image_to_text('scan0015.tiff', language='Russian')

    """
    import os
    import subprocess
    if not os.path.exists(path):
        raise ValueError('File {0} does not exist.'.format(path))
    args = ['cuneiform', '-o', OUT_FILENAME, path]
    if language:
        args += ['-l', language[:3].lower()]
    print args
    process = subprocess.Popen(args)
    return_code = process.wait()
    if return_code:
        raise RuntimeError('OCR parsing failed.')
    f = open(OUT_FILENAME)
    result = f.read().strip()
    result = result.decode('utf-8')
    f.close()
    os.unlink(OUT_FILENAME)
    return result
'''
