#!/usr/bin/env python

from sumomomig.utils import write_out, read_in


def main():

    data = read_in('dump')

    bad_img_links = []
    img_titles = [i.title for i in data['images']]
    for link in sorted(data['links'], key=lambda t: t.kind):
        if link.kind == 'Image':
            if link.target not in img_titles:
                bad_img_links.append(link)

    doc_title_map = {}
    for doc in data['docs']:
        doc_title_map.setdefault(doc['title'], []).append(doc)

    # Check for links to articles or images that don't exist.
    bad_doc_links = []
    for link in [d for d in data['links']
                 if d.kind in ['Article', 'Template']]:
        if link.target is None:
            continue
        if link.kind == 'Template':
            link.target = 'Template:' + link.target
        if link.target not in doc_title_map:
            bad_doc_links.append(link)

    # Print stats about bad image links.
    if len(bad_img_links) > 0:
        badc = len(bad_img_links)
        totc = len([l for l in data['links'] if l.kind == 'Image'])
        print("{0}/{1} image links are bad ({2}%)."
              .format(badc, totc, int(badc / totc * 100)))

    # Print stats about bad article links.
    if len(bad_doc_links) > 0:
        badc = len(bad_doc_links)
        totc = len([l for l in data['links']
                   if l.kind in ['Article', 'Template']])
        print("{0}/{1} document links are bad ({2}%)."
              .format(badc, totc, int(badc / totc * 100)))

    # Check for docs with duplicate parents:
    parents = set()
    for doc in data['docs']:
        if 'parent' not in doc:
            continue
        else:
            par = doc['parent']
            val = (par['title'], par['slug'], par['locale'], doc['locale'])
            if val in parents:
                print('Document "{title}" has a duped parent.'.format(**doc))
                print(val)
            else:
                parents.add(val)

    # Nothing changed, but keep the pipeline flowing.
    write_out(data, 'validate')


if __name__ == '__main__':
    main()
