#!/usr/bin/env python

import sys

sys.path.append('..')

from sumomomig.utils import write_out, read_in, Image, get_db, config


def main():
    data = read_in('validate')

    conn, cur = get_db()

    cur.execute(
        '''
        SELECT title, locale, description, file, thumbnail
        FROM {sumo_db}.gallery_image
        '''
        .format(sumo_db=config('db', 'sumo_db')))

    sumo_images = list(Image(*t) for t in cur)
    sumo_image_title_locales = set()
    sumo_image_paths = set()

    for img in sumo_images:
        sumo_image_title_locales.add((img.title.lower(), img.locale))
        sumo_image_paths.add(img.file)
        if img.thumbnail:
            sumo_image_paths.add(img.thumbnail)

    image_collisions = {}

    panic = False
    for img in data['images']:
        title_locale = (img.title.lower(), img.locale)

        if title_locale in sumo_image_title_locales:
            image_collisions[title_locale] = img.title
            old_title = img.title
            img.title += ' TB'
            print('> changed img "{0}" to "{1}"'.format(old_title, img.title))

        if img.file in sumo_image_paths:
            print('AHHHH, duplicate file!', img.file)
            panic = True

        if img.thumbnail and img.thumbnail in sumo_image_paths:
            print('AHHHH, duplicate thumbnail!', img.thumbnail)
            panic = True

    if panic:
        print('Panicking.')
        # sys.exit(1)

    cur.execute(
        '''
        SELECT title, slug, locale
        FROM {sumo_db}.wiki_document
        '''
        .format(sumo_db=config('db', 'sumo_db')))

    sumo_doc_titles = []
    sumo_doc_slugs = []

    for title, slug, locale in cur:
        sumo_doc_titles.append((title.lower(), locale))
        sumo_doc_slugs.append((slug.lower(), locale))

    title_collision_count = 0
    slug_collision_count = 0
    title_changes = {}

    for doc in data['docs']:
        title_locale = (doc['title'].lower(), doc['locale'])
        slug_locale = (doc['slug'].lower(), doc['locale'])

        if title_locale in sumo_doc_titles:
            new_name = doc['title'] + ' TB'
            title_changes[doc['title']] = new_name
            doc['title'] = new_name
            title_collision_count += 1

        if slug_locale in sumo_doc_slugs:
            doc['slug'] += '-tb'
            slug_collision_count += 1

        for link in [l for l in doc['links'] if l.kind == 'Image']:
            title_locale = (link.target, link.locale)
            if title_locale in image_collisions:
                old_title = image_collisions[title_locale]
                new_title = old_title + ' TB'
                title_changes[old_title] = new_title

    print(len(image_collisions.keys()), 'image collisions')
    print(title_collision_count, 'document title collisions')
    print(slug_collision_count, 'document slug collisions')

    cur.close()
    conn.close()

    for doc in data['docs']:
        for link in doc['links']:
            if link.target in title_changes:
                old = str(link)
                link.target = title_changes[link.target]
                new = str(link)
                doc['content'] = doc['content'].replace(old, new)
        if doc.get('parent', {}).get('title') in title_changes:
            doc['parent']['title'] = title_changes[doc['parent']['title']]

    write_out(data, 'uncollide')


if __name__ == '__main__':
    main()
