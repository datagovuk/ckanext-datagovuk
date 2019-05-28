import ckan.logic.schema
from ckan.plugins.toolkit import (
    check_access,
    navl_validate,
    ValidationError,
    get_action,
    )
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.logic.action.create import resource_create as resource_create_core
from ckan.logic import get_or_bust
from ckanext.datagovuk.lib.organogram_xls_splitter import create_organogram_csvs

import cgi
import mimetypes
from datetime import date, datetime

log = __import__('logging').getLogger(__name__)


# defined as they are in ckan/action/create.py to save further hacks to the
# function copied from there
_check_access = check_access
_validate = navl_validate

class FakeFieldStorage(cgi.FieldStorage):
    def __init__(self, destination_filename, stream):
        self.name = 'upload'
        self.filename = destination_filename
        self.file = stream
        self.file.seek(0)

def resource_create(context, data_dict):
    '''Wraps the original CKAN resource creation
    to handle XLS organogram uploads and split them into
    component CSVs.

    Passes all non-organogram resources through to CKAN
    as normal.

    See ckan.logic.action.create.resource_create for
    documentation on the original function.
    '''
    mimetype = mimetypes.guess_type(data_dict['url'])[0]
    log.debug("Mimetype: %s" % mimetype)

    if mimetype == 'application/vnd.ms-excel':
        log.debug("Excel file detected")

        package_id = get_or_bust(data_dict, 'package_id')

        pkg_dict = get_action('package_show')(
            dict(context, return_type='dict'),
            {'id': package_id})

        organogram_ids = {
            '538b857a-64ba-490e-8440-0e32094a28a7', # Local authority
            'd3c0b23f-6979-45e4-88ed-d2ab59b005d0', # Departmental
            }

        if pkg_dict.get('schema-vocabulary') in organogram_ids:
            log.debug("Organogram detected")

            file_handle = data_dict['upload'].file

            errors, warnings, senior_csv, junior_csv = create_organogram_csvs(file_handle)

            # table = Table('path.csv', schema='schema.json')

            if errors:
                context['session'].rollback()
                raise ValidationError(errors)
            else:
                log.debug("Valid organogram Excel file found")
                timestamp = datetime.utcnow()
                timestamp_str = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")

                senior_resource = _create_csv_resource('Senior', senior_csv, data_dict.copy(), context, timestamp_str)
                junior_resource = _create_csv_resource('Junior', junior_csv, data_dict.copy(), context, timestamp_str)

                print('dgu resource_create', senior_resource)

                resource = senior_resource

                print('dgu resource_create resource', resource)
                # if isinstance(resource.get('upload', None), cgi.FieldStorage):
                #     print('resource_create body start', body)
                #     log.info("File is being uploaded")
                #     resource['upload'].file.seek(0)
                #     body = resource['upload'].file
                #     print('resource_create body', body)
                # # If resource.get('url_type') == 'upload' then the resource is in CKAN file system
                # elif resource.get('url_type') == 'upload':
                #     print('in ckan')

                try:
                    import os
                    import requests
                    # Start session to download files
                    session = requests.Session()
                    log.info("Attempting to obtain resource %s from url %s" % (resource.get('name',''), resource.get('url', '')))
                    response = session.get(
                        resource.get('url', ''), timeout=30)
                    # If the response status code is not 200 (i.e. success), raise Exception
                    if response.status_code != 200:
                        log.error("Error obtaining resource from the given URL. Response status code is %d" % response.status_code)
                        # raise Exception("Error obtaining resource from the given URL. Response status code is %d" % response.status_code)
                    # body = response.content
                    log.info("Successfully obtained resource %s from url %s" % (resource.get('name',''), resource.get('url', '')))
                    # print(body)

                    from tableschema import Table
                    d = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
                    full_path = os.path.join(d, "senior_csv_schema.json")
                    print(full_path)
                    table = Table(resource.get('url', ''), schema=full_path)
                    print(table.schema.descriptor)
                    print('schema:', table.schema.valid)

                    # table.read(keyed=True)

                except requests.exceptions.RequestException:
                    print('not found')

                # from ckanext.datagovuk.schemas.

                return senior_resource

    log.debug("Passing args through to the CKAN resource_create")
    return resource_create_core(context, data_dict)

def _create_csv_resource(junior_senior, csv, resource_data, context, timestamp):
    filename = 'organogram-%s.csv' % junior_senior.lower()
    csv_wrapper = FakeFieldStorage(filename, csv)
    _date = resource_data.get('datafile-date')

    if not _date:
        today = date.today()
        _date = today.strftime("%Y-%m-%d")

    resource_data['name'] = '{} Organogram ({})'.format(_date, junior_senior)
    resource_data['url'] = filename
    resource_data['upload'] = csv_wrapper
    resource_data['timestamp'] = timestamp

    res = resource_create_core(context, resource_data)

    print('_create_csv_resource', resource_data)
    print('_create_csv_resource csv_wrapper', csv_wrapper)

    return res


def user_create(context, data_dict):
    '''Create a new user.

    You must be authorized to create users.

    :param name: the name of the new user, a string between 2 and 100
        characters in length, containing only lowercase alphanumeric
        characters, ``-`` and ``_``
    :type name: string
    :param email: the email address for the new user
    :type email: string
    :param password: the password of the new user, a string of at least 4
        characters
    :type password: string
    :param id: the id of the new user (optional)
    :type id: string
    :param fullname: the full name of the new user (optional)
    :type fullname: string
    :param about: a description of the new user (optional)
    :type about: string
    :param openid: (optional)
    :type openid: string

    :returns: the newly created user
    :rtype: dictionary

    '''
    model = context['model']
    schema = context.get('schema') or ckan.logic.schema.default_user_schema()
    session = context['session']

    _check_access('user_create', context, data_dict)

    data, errors = _validate(data_dict, schema, context)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    # user schema prevents non-sysadmins from providing password_hash
    if 'password_hash' in data:
        data['_password'] = data.pop('password_hash')

    user = model_save.user_dict_save(data, context)

    # Flush the session to cause user.id to be initialised, because
    # activity_create() (below) needs it.
    session.flush()

    activity_create_context = {
        'model': model,
        'user': context['user'],
        'defer_commit': True,
        'ignore_auth': True,
        'session': session
    }
    activity_dict = {
        'user_id': user.id,
        'object_id': user.id,
        'activity_type': 'new user',
    }
    get_action('activity_create')(activity_create_context, activity_dict)

    if not context.get('defer_commit'):
        model.repo.commit()

    # A new context is required for dictizing the newly constructed user in
    # order that all the new user's data is returned, in particular, the
    # api_key.
    #
    # The context is copied so as not to clobber the caller's context dict.
    user_dictize_context = context.copy()
    user_dictize_context['keep_apikey'] = True
    user_dictize_context['keep_email'] = True
    user_dict = model_dictize.user_dictize(user, user_dictize_context)

    context['user_obj'] = user
    context['id'] = user.id

    model.Dashboard.get(user.id)  # Create dashboard for user.

    # DGU Hack: added encoding so we don't barf on unicode user names
    log.debug('Created user {name}'.format(name=user.name.encode('utf8')))
    return user_dict
