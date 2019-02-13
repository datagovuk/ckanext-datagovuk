#! /bin/bash

pip=${1-'/usr/bin/env pip'}

ckan_harvest_fork='ckan'
ckan_harvest_sha='5aad13c2f9aba738a82eeca8bb7a859e584f483b'

ckan_dcat_fork='ckan'
ckan_dcat_sha='v0.0.8'

ckan_spatial_fork='alphagov'
ckan_spatial_sha='waf-fix'

ckan_s3_resources_fork='alphagov'
ckan_s3_resources_sha='50341b3960a6be3aba5a1558e80dd9a8c7c70c2c'

ckan_fork='ckan'
ckan_sha='ckan-2.7.4'

$pip install -U pip

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt)
$pip install -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_dcat_fork/ckanext-dcat/$ckan_dcat_sha/requirements.txt)
$pip install -U "git+https://github.com/$ckan_dcat_fork/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt)
$pip install -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_s3_resources_fork/ckanext-s3-resources/$ckan_s3_resources_sha/requirements.txt)
$pip install -U "git+https://github.com/$ckan_s3_resources_fork/ckanext-s3-resources@$ckan_s3_resources_sha#egg=ckanext-s3-resources"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt)
$pip install -r https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt
$pip install -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan"

$pip install -r requirements.txt
