import ckan.logic.schema
from ckan.logic.action.get import organization_show, package_search, package_show
from ckan.plugins.toolkit import (
    abort,
    check_access,
    navl_validate,
    side_effect_free,
    ValidationError,
    get_action,
)
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize

from ckan.model import User

from ckanext.datagovuk.pii_helpers import remove_pii, remove_pii_from_list

log = __import__('logging').getLogger(__name__)


# defined as they are in ckan/action/get.py to save further hacks to the
# function copied from there
_check_access = check_access


def user_auth(context, data_dict):
    '''Authenticates a user

    You must be a system administrator to authenticate users.

    :param email: the email address of the user
    :type email: string
    :param password: the password of the user
    :type password: string

    :returns: the newly created user
    :rtype: dictionary

    '''
    model = context['model']
    session = context['session']

    _check_access('user_auth', context, data_dict)

    email = data_dict.get('email')
    password = data_dict.get('password')

    if not (email and password):
        raise ValidationError(['email and password are both required'])

    users = User.by_email(email)
    user = users[0] if users else None

    if (user is None) or \
            (not user.is_active()) or \
            (not user.validate_password(password)):
        raise ValidationError(['There was a problem authenticating this user'])

    user_dict = model_dictize.user_dictize(user, context)

    ## Get the user's organisation list to return with the login details
    fOrgList = get_action('organization_list_for_user')
    user_dict['organisations'] = fOrgList(context, {'id': user.name})

    # DGU Hack: added encoding so we don't barf on unicode user names
    log.debug('Authenticated user {name}'.format(name=user.name.encode('utf8')))
    return user_dict


@side_effect_free
def dgu_package_search(context, data_dict):
    return remove_pii_from_list(package_search(context, data_dict))


@side_effect_free
def dgu_package_show(context, data_dict):
    return remove_pii(package_show(context, data_dict))


@side_effect_free
def dgu_organization_show(context, data_dict):
    data_dict['include_users'] = False
    return remove_pii(organization_show(context, data_dict))
