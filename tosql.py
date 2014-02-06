#!/usr/bin/env python

import sys
from numbers import Number
from textwrap import dedent

sys.path.append('..')

from sumomomig.utils import read_in, Link


def main():
    data = read_in('uncollide')
    sql = prelude()

    # Sort so that English documents come first.
    # This is important because English will have no parents, and every
    # non-English document will have a parent that is an English document.
    sorted_docs = sorted(data['docs'],
                         key=lambda doc: 0 if doc['locale'] == 'en-US' else 1)

    for doc in sorted_docs:
        sql += doc_to_sql(doc)

    for img in data['images']:
        sql += img_to_sql(img)

    sql += finale()

    sql = sql.format(sumo_db='kitsune')

    with open('sumomo.sql', 'w') as f:
        f.write(sql)


def prelude():
    return dedent('''\
        START TRANSACTION;

        INSERT INTO {sumo_db}.auth_user
            (username, first_name, last_name, email, password, is_staff,
             is_active, is_superuser, last_login, date_joined)
            VALUES ("thunderbird_migration", "", "", "support@mozilla.org",
                    "", 0, 1, 0, CURDATE(), CURDATE());
        SET @tb_user_id = LAST_INSERT_ID();

        SET @tb_product_id = (SELECT id
                              FROM {sumo_db}.products_product
                              WHERE slug = "thunderbird"
                              LIMIT 1);
    ''') + '\n'


def finale():
    return '\nROLLBACK;'


def doc_to_sql(doc):
    tmpl = dedent('''\
        INSERT INTO {{sumo_db}}.wiki_document
            (title, locale, slug, html, is_archived, needs_change,
             needs_change_comment, category)
            VALUES ("{title}",
                    "{locale}",
                    "{slug}",
                    "",
                    0,
                    0,
                    "",
                    {category}
                    );
        SET @doc_id = LAST_INSERT_ID();

        INSERT INTO {{sumo_db}}.wiki_revision
            (document_id, summary, content, keywords, created, reviewed,
             significance, comment, creator_id, reviewer_id, is_approved,
             is_ready_for_localization, readied_for_localization,
             readied_for_localization_by_id)
            VALUES (@doc_id,
                    "{summary}",
                    "{content}",
                    "{keywords}",
                    CURDATE(),
                    CURDATE(),
                    30,
                    CONCAT("Import from SUMOMO - ", CURDATE(), CURTIME()),
                    @tb_user_id,
                    @tb_user_id,
                    1,
                    1,
                    CURDATE(),
                    @tb_user_id
                    );
        SET @rev_id = LAST_INSERT_ID();

        UPDATE {{sumo_db}}.wiki_document
            SET current_revision_id = @rev_id,
                latest_localizable_revision_id = @rev_id
            WHERE id = @doc_id;

        INSERT INTO {{sumo_db}}.wiki_document_products
            (document_id, product_id)
            VALUES(@doc_id, @tb_product_id);
    ''') + '\n'

    if 'parent' in doc:
        tmpl += dedent('''\
            SET @parent_id = (SELECT id
                              FROM {{sumo_db}}.wiki_document
                              WHERE title = "{parent[title]}"
                                AND slug = "{parent[slug]}"
                                AND locale = "{parent[locale]}");
            UPDATE {{sumo_db}}.wiki_document
                SET parent_id = @parent_id
                WHERE id = @doc_id;
        ''') + '\n'

    if doc['significance'] is None:
        doc['significance'] = 0

    return tmpl.format(**escape(doc))


def img_to_sql(img):
    tmpl = dedent('''\
        INSERT INTO {{sumo_db}}.gallery_image
            (title, created, updated, description, locale, creator_id,
             file, thumbnail, is_draft)
            VALUES ("{title}",
                    CURDATE(),
                    CURDATE(),
                    "{description}\\n\\nImported from SUMOMO",
                    "{locale}",
                    @tb_user_id,
                    "{file}",
                    "{thumbnail}",
                    NULL);
        ''') + '\n'

    return tmpl.format(**escape(img.as_dict()))


def escape(obj):
    to_str = set([Link])

    if isinstance(obj, dict):
        return {key: escape(val) for key, val in obj.items()}
    elif isinstance(obj, list):
        return [escape(val) for val in obj]
    elif isinstance(obj, str):
        return (obj.replace('\\', '\\\\')
                   .replace('"', '\\"')
                   .replace('{', '{{')
                   .replace('}', '}}'))
    elif isinstance(obj, Number):
        return obj
    elif type(obj) in to_str:
        return str(obj)
    else:
        raise TypeError("I don't know how to escape a " + str(type(obj)))


if __name__ == '__main__':
    main()
