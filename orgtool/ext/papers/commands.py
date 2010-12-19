# -*- coding: utf-8 -*-

import os
import Image
from argh import *
from tool import app

from schema import Page


IMAGE_FORMATS = 'JPEG', 'PNG', 'GIF'
TMP_FILENAME = '__tmp-'+__name__


@arg('paths', nargs='+')
@arg('-l', '--language')
@arg('-s', '--summary')
@arg('--summary-prefix', help='add this prefix to summary')
@arg('-f', '--format', help='convert image to given format')
@arg('--skip-ocr-errors', default=False, help='skip OCR if it cannot be done')
@arg('--no-ocr', default=False, help='do not try parsing with OCR')
def add_pages(args):
    _args_to_unicode(args, ['language', 'summary', 'summary_prefix'])
    db = app.get_feature('document_storage').default_db

    # check if the files exist
    for path in args.paths:
        assert os.path.exists(path)

    # import
    for path in args.paths:
        yield '* importing {0} (language {1})'.format(path, args.language)

        fingerprint = get_file_hash(open(path, 'rb'))

        # check file hash uniqueness
        if Page.objects(db).where(source_fingerprint=fingerprint):
            yield '...already in the database.'
            continue

        p = Page()

        p.summary = args.summary or get_summary_from_path(path)
        if args.summary_prefix:
            p.summary = u'{0} {1}'.format(args.summary_prefix, p.summary)
        p.language = args.language or None
        p.source_fingerprint = fingerprint
        if not args.no_ocr:
            try:
                p.details = image_to_text(path=path, language=p.language)
            except RuntimeError as e:
                if not args.skip_ocr_errors:
                    raise CommandError(e)
                yield '(OCR failed, saving only image itself)'

        # usually we don't need heavy formats like ppm or tiff even for OCR
        img = Image.open(path)
        if args.format:
            fmt = args.format
        elif img.format not in IMAGE_FORMATS:
            fmt = IMAGE_FORMATS[0]
        else:
            fmt = img.format
        img.save(TMP_FILENAME, fmt)
        p['image'] = open(TMP_FILENAME, 'rb')
        # provide original path so that the resulting filename is inherited
        p['image'].path = path

        p.save(db)


@arg('-k', '--pk', help='Page primary key')
@arg('-p', '--path', help='File path')
@arg('-s', '--save', default=False, help='Save result to the Page (with --pk)')
@arg('-l', '--language', help='Language of the text (improves recognition)')
def ocr(args):
    """Performs optical character recognition (OCR) on given image. The image
    can be defined either as path to a file or as the primary key of a Page
    object. The latter case also enables saving the resulting text to the
    object. By default the result is simply printed.
    """
    try:
        assert args.pk or args.path, '--path or --pk must be provided'
        assert not (args.pk and args.path), 'specify either --path or --pk'
        assert not (args.path and args.save), 'use --save only with --pk'
    except AssertionError as e:
        raise CommandError(e)

    if args.pk:
        db = app.get_feature('document_storage').default_db
        page = Page.object(db, args.pk)
        path = page.image.full_path
    else:
        path = args.path

    text = image_to_text(path, language=args.language)

    if args.save:
        page.details = text
        page.save()
        yield 'Page saved with the new text.'
    else:
        yield text


#-----------#
#  Helpers  #
#-----------#

def get_summary_from_path(path):
    path = os.path.splitext(os.path.split(path)[1])[0].decode('utf-8')
    return u'(scan) {0}'.format(path)

def get_file_hash(stream):
#        path = self['image'].path
#        if not path:
#            return None
        #content = open(path).read()
#    content = self['image'].file.fp.read()
#    self['image'].file.seek(0)  # rewind
    import hashlib
    data = stream.read()
    return hashlib.md5(data).hexdigest()

### OCR stuff

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
    process = subprocess.Popen(args)
    return_code = process.wait()
    if return_code:
        raise RuntimeError('OCR parsing failed.')
    f = open(OUT_FILENAME)
    result = f.read().strip()
    result = result.decode('utf-8', 'replace')
    f.close()
    os.unlink(OUT_FILENAME)
    return result

def _args_to_unicode(namespace, names):
    for name in names:
        value = getattr(namespace, name, None)
        if value is not None:
            setattr(namespace, name, value.decode('utf8'))
