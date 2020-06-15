#!/usr/bin/env sh

set -ex

venv/bin/pip install -r venv/src/ckan/dev-requirements.txt
venv/bin/pip install -r dev-requirements.txt
dropdb ckan_test; createdb ckan_test
venv/bin/python setup.py develop

curl http://127.0.0.1:8983/solr/admin/collections?action=LIST

paster --plugin=ckan db init -c test-jenkins.ini
paster --plugin=ckanext-harvest harvester initdb -c test-jenkins.ini

export TEST_CKAN_INI=test-jenkins.ini
bin/run-tests.sh
