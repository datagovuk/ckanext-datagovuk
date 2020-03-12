#! /bin/bash

pip=${1-'/usr/bin/env pip'}

ckan_harvest_sha='713a0fb04ff790d847824df427fa40a3f91bbc7c'

ckan_dcat_sha='b757e5be643a17f08b1bb102348c370abee149d5'

ckan_spatial_fork='alphagov'
ckan_spatial_sha='c35e1249cfb3c7b2f1286f433fd51c6fe8f05b72'

ckan_sha='ckan-2.7.4'

pycsw_tag='2.4.0'

$pip install -U pip

$pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt)
$pip install -U "git+https://github.com/ckan/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest"

$pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-dcat/$ckan_dcat_sha/requirements.txt)
$pip install -U "git+https://github.com/ckan/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt)
$pip install -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

$pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckan/$ckan_sha/requirement-setuptools.txt)
$pip install -r https://raw.githubusercontent.com/ckan/ckan/$ckan_sha/requirements.txt
$pip install -Ue "git+https://github.com/ckan/ckan.git@$ckan_sha#egg=ckan"

$pip install -r requirements.txt

$pip install -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw.git/$pycsw_tag/requirements.txt)
$pip install -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_tag#egg=pycsw"

pycsw_src="$(/usr/bin/env python -m site | grep pycsw | sed "s:[ |,|']::g")"
(cd $pycsw_src && /usr/bin/env python setup.py build)
$pip install -e .
