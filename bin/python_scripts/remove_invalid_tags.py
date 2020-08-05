#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Set up environment from ckan.ini
# export POSTGRES_URL=<sqlalchemy.url from ckan.ini>
#
# Execute script like this -
# python remove_invalid_tags.py
#

import csv, io, logging, os, psycopg2, subprocess, sys
from datetime import datetime

from ckan.logic.schema import default_tags_schema
from ckan.lib.navl.dictization_functions import validate
from ckan.model.types import make_uuid

POSTGRES_URL = os.environ['POSTGRES_URL']

logger = logging.getLogger(__name__)
connection = psycopg2.connect(POSTGRES_URL)


def setup_logging():
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(_format)
    logger.addHandler(c_handler)

    f_handler = logging.FileHandler('remove_invalid_tags.log')
    f_handler.setFormatter(_format)
    logger.addHandler(f_handler)

    logger.info('====================================================================')


def is_dev():
    return '@db' in POSTGRES_URL


def remove_invalid_tags(live=False):
    if not os.path.isfile("invalid_tags_data.csv"):
        logger.error("'invalid_tags_data.csv' not found, run 'python find_invalid_tags.py' to generate it")
        return

    invalid_tags = []

    package_tag_revision_sql = "DELETE FROM package_tag_revision WHERE tag_id = '{}';"
    package_tag_sql = "DELETE FROM package_tag WHERE tag_id = '{}';"
    tag_sql = "DELETE FROM tag WHERE id = '{}';"
    confirm_sql = "SELECT id FROM tag WHERE id='{}';"
    get_harvest_object_sql = "SELECT id FROM harvest_object WHERE package_id = %s;"
    check_error_sql = "SELECT id FROM harvest_object_error WHERE harvest_object_id = %s AND message = %s;"
    insert_error_sql = "INSERT INTO harvest_object_error (id, harvest_object_id, message, stage, created) " \
        "VALUES (%s, %s, %s, %s, %s);"

    try:
        cursor = connection.cursor()
        with io.open("invalid_tags_data.csv", "rb") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['tag_id'] in invalid_tags:
                    continue
                invalid_tags.append(row['tag_id'])

                if not live:
                    logger.info(
                        "DB - Would have executed: %s to remove '%s'",
                        ", ".join([
                            package_tag_revision_sql.format(row['tag_id']),
                            package_tag_sql.format(row['tag_id']),
                            tag_sql.format(row['tag_id'])]
                        ),
                        row["tag_name"]
                    )
                    continue

                cursor.execute(confirm_sql.format(row['tag_id']))
                if not cursor.fetchone():
                    logger.info("DB - Tag not found '%s'", row['tag_name'])
                    continue

                cursor.execute('BEGIN TRANSACTION;')
                cursor.execute(package_tag_revision_sql.format(row['tag_id']))
                cursor.execute(package_tag_sql.format(row['tag_id']))
                cursor.execute(tag_sql.format(row['tag_id']))
                cursor.execute('COMMIT TRANSACTION;')

                cursor.execute(get_harvest_object_sql, (row["package_id"],))
                res = cursor.fetchone()
                if not res:
                    logger.error('DB - Harvest object not found for package %s', row["package_id"])
                    continue
                harvest_object_id, = res

                cursor.execute(check_error_sql, (harvest_object_id, row["errors"]))
                if cursor.fetchone():
                    logger.info("DB - Harvest object error for tag: '%s' already created", row["tag_name"])
                    continue

                cursor.execute(
                    insert_error_sql, 
                    (
                        make_uuid(),
                        harvest_object_id,
                        row['errors'],
                        "Validation",
                        datetime.now()
                    )
                )
                connection.commit()

                cursor.execute(confirm_sql.format(row['tag_id']))
                res = cursor.fetchone()
                logger.info(
                    "DB - %s executing %s, removing '%s'",
                    "SUCCESS" if not res else "FAILED",
                    ", ".join([
                        package_tag_revision_sql.format(row['tag_id']),
                        package_tag_sql.format(row['tag_id']),
                        tag_sql.format(row['tag_id'])]
                    ),
                    row["tag_name"]
                )

                if not res:
                    logger.info("SOLR - reindexing %s", row['package_id'])
                    paster_command = 'paster --plugin=ckan search-index rebuild {} --config {}'.format(
                        row['package_id'], '/srv/app/production.ini' if is_dev() else '/var/ckan/ckan.ini')
    finally:
        cursor.close()

def main(command=None):
    while command not in ['live', 'dry-run']:
        command = raw_input(
            '(Options: dry-run, live): dry-run? ')
        if not command:
            command = 'dry-run'

    setup_logging()

    logger.info('Remove invalid tags')
    logger.info('====================================================================')

    remove_invalid_tags(command == 'live')

    logger.info('====================================================================')
    logger.info('Processing complete')

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
