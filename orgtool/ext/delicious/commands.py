# -*- coding: utf-8 -*-

# TODO: curl https://user:passwd@api.del.icio.us/v1/posts/all
# see http://delicious.com/help/api#posts_all for API info

import datetime
import os
import xml.dom.minidom
from doqu import Document, Field as f
from tool import app
from tool.cli import command
from tool.ext.templating import register_templates
from tool.ext import admin
from orgtool.ext.notes.schema import Bookmark


@command
def import_dump(path):
    "Imports an XML dump of all your bookmarks on delicious.com"
    assert os.path.exists(path)
    db = app.get_feature('document_storage').default_db
    x = xml.dom.minidom.parse(path)
    posts = x.documentElement.getElementsByTagName('post')
    seen_cnt = saved_cnt = 0
    for post in posts:
        seen_cnt += 1
        data = dict(post.attributes.items())
        if Bookmark.objects(db).where(url=data['href']).count():
            continue
        bookmark = Bookmark(
            url = data['href'],
            summary = data['description'],
            details = data['extended'],
            tags = data['tag'].split(),
            date_time = datetime.datetime.strptime(data['time'],
                                            '%Y-%m-%dT%H:%M:%SZ'),
            shared = False if data.get('shared')=='no' else True,
        )
        # FIXME: check uniqueness
        print u'Saving {date_time} {url}...'.format(**bookmark)
        pk = bookmark.save(db)
        saved_cnt +=1
    print 'Saved {saved_cnt} bookmarks of {seen_cnt}.'.format(**locals())
