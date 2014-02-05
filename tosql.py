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
        # print(doc)
        sql += doc_to_sql(doc)

    sql += finale()

    with open('out', 'w') as f:
        f.write(sql)
    sql = sql.format(sumo_table='kitsune')

    with open('sumomo.sql', 'w') as f:
        f.write(sql)


def prelude():
    return dedent('''\
        START TRANSACTION;

        INSERT INTO {sumo_table}.auth_user
            (username, first_name, last_name, email, password, is_staff,
             is_active, is_superuser, last_login, date_joined)
            VALUES ("thunderbird_migration", "", "", "support@mozilla.org",
                    "", 0, 1, 0, CURDATE(), CURDATE());
        SET @tb_user = LAST_INSERT_ID();
    ''') + '\n'


def finale():
    return '\nROLLBACK;'


def doc_to_sql(doc):
    tmpl = dedent('''\
        INSERT INTO {{sumo_table}}.wiki_document
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

        INSERT INTO {{sumo_table}}.wiki_revision
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
                    {significance},
                    CONCAT("Import from SUMOMO - ", CURDATE(), CURTIME()),
                    @tb_user,
                    @tv_user,
                    1,
                    1,
                    CURDATE(),
                    @tb_user
                    );
        SET @rev_id = LAST_INSERT_ID();

        UPDATE {{sumo_table}}.wiki_document
            SET current_revision_id = @rev_id,
                latest_localizable_revision_id = @rev_id
            WHERE id = @doc_id;
    ''') + '\n'

    if 'parent' in doc:
        tmpl += dedent('''\
            SET @parent_id = (SELECT id
                              FROM {{sumo_table}}.wiki_document
                              WHERE title = "{parent[title]}"
                                AND slug = "{parent[slug]}"
                                AND locale = "{parent[locale]}");
            UPDATE {{sumo_table}}.wiki_document
                SET parent_id = @parent_id
                WHERE id = @doc_id;
        ''') + '\n'

    if doc['significance'] is None:
        doc['significance'] = 0

    return tmpl.format(**escape(doc))


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
