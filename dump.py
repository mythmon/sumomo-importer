#!/usr/bin/env python

import sys
sys.path.append('..')

import re

from sumomomig.utils import Link, Image, write_out, get_db, config


def rows(cursor):
    column_names = [t[0] for t in cursor.description]
    for row in cursor:
        yield {key: val for key, val in zip(column_names, row)}


def identify_link(linktext, slug, locale):
    linktext = linktext[2:-2]
    url_hash = None

    if ':' in linktext:
        kind, target = linktext.split(':', 1)
    else:
        kind = 'Article'
        target = linktext

    if '|' in target:
        target, extra = target.split('|', 1)
    else:
        extra = None

    if '#' in target:
        target, url_hash = target.split('#')
        url_hash = '#' + url_hash

    if target == '':
        target = None

    if kind == 'T':
        kind = 'Template'
    if kind == 'http':
        kind = 'External'
        target = 'http:' + target

    return Link(kind, target, extra, slug, locale, url_hash)


def doc_from_row(row):
    if row['doc__is_template']:
        assert row['doc__title'].startswith('Template:')
    # if row['doc__is_localizable']:
    #     cur_rev = row['doc__current_revision_id']
    #     latest_localizable = row['doc__latest_localizable_revision_id']
    #     assert cur_rev == latest_localizable

    links = re.findall(r'\[\[[^\]]+\]\]', row['rev__content'])
    links = [identify_link(l, row['doc__slug'], row['doc__locale'])
             for l in links]

    d = {
        'title': row['doc__title'],
        'slug': row['doc__slug'],
        'locale': row['doc__locale'],
        'category': row['doc__category'],
        'is_localizable': row['doc__is_localizable'],
        'is_template': row['doc__is_template'],
        'content': row['rev__content'],
        'author': row['creator__username'],
        'links': links,
        'summary': row['rev__summary'],
        'comment': row['rev__comment'],
        'keywords': row['rev__keywords'],
        'significance': row['rev__significance'],
    }

    if 'parent_doc__title' in row:
        d['parent'] = {
            'title': row['parent_doc__title'],
            'slug': row['parent_doc__slug'],
            'locale': row['parent_doc__locale'],
        }

    return d


def process_docs(cur, query):
    cur.execute(query)
    docs = []
    links = set()
    for row in rows(cur):
        doc = doc_from_row(row)
        docs.append(doc)
        links.update(doc['links'])
    return docs, links


def main():
    output = {
        'docs': [],
        'links': set(),
        'images': set(),
    }

    select_keys = []
    select_keys.extend('doc.' + key for key in [
        'id', 'title', 'slug', 'is_template', 'is_localizable', 'locale',
        'current_revision_id', 'latest_localizable_revision_id', 'parent_id',
        'html', 'category', 'is_archived', 'allow_discussion'])

    select_keys.extend('rev.' + key for key in [
        'id', 'document_id', 'summary', 'content', 'keywords', 'created',
        'reviewed', 'significance', 'comment', 'reviewer_id', 'creator_id',
        'is_approved', 'based_on_id', 'is_ready_for_localization'])

    select_keys.extend('creator.' + key for key in [
        'id', 'username', 'first_name', 'last_name', 'email', 'is_staff',
        'is_active', 'is_superuser', 'last_login', 'date_joined'])

    # select_keys.extend('creator_prof.' + key for key in [
    #     'user_id', 'name', 'public_email', 'avatar', 'bio', 'website',
    #     'twitter', 'facebook', 'irc_handle', 'timezone', 'country', 'city',
    #     'livechat_id', 'locale'])
    #
    # # sumomo.users_profile as creator_prof)
    #
    # # AND creator.id = creator_prof.user_id)

    conn, cur = get_db()

    # en-US
    docs, links = process_docs(
        cur,
        '''
        SELECT {select_keys}
        FROM {sumomo_db}.wiki_document as doc
        JOIN ({sumomo_db}.wiki_revision as rev,
             {sumomo_db}.auth_user as creator)
        ON (rev.id = doc.current_revision_id
            AND creator.id = rev.creator_id)
        WHERE doc.is_archived = 0
            AND doc.locale = 'en-US'
        '''
        .format(sumomo_db=config('db', 'sumomo_db'),
                select_keys=', '.join('{0} as {1}'
                                      .format(key, key.replace('.', '__'))
                                      for key in select_keys)))
    output['docs'].extend(docs)
    output['links'].update(links)

    # Non en-US
    select_keys.extend('parent_doc.' + k for k in ['title', 'slug', 'locale'])
    docs, links = process_docs(
        cur,
        '''
        SELECT {select_keys}
        FROM {sumomo_db}.wiki_document as doc
        JOIN ({sumomo_db}.wiki_revision as rev,
             {sumomo_db}.auth_user as creator,
             {sumomo_db}.wiki_document as parent_doc)
        ON (rev.id = doc.current_revision_id
            AND creator.id = rev.creator_id
            AND doc.parent_id = parent_doc.id)
        WHERE doc.is_archived = 0
          AND doc.locale != 'en-US'
        '''
        .format(sumomo_db=config('db', 'sumomo_db'),
                select_keys=', '.join('{0} as {1}'
                                      .format(key, key.replace('.', '__'))
                                      for key in select_keys)))
    output['docs'].extend(docs)
    output['links'].update(links)

    cur.execute(
        '''
        SELECT title, locale, description, file, thumbnail
        FROM {sumomo_db}.gallery_image;
        '''
        .format(sumomo_db=config('db', 'sumomo_db')))
    output['images'].update(Image(*i) for i in cur)

    write_out(output, 'dump')

    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
