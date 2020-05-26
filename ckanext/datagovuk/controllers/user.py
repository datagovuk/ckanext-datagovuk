from ckan.controllers.user import UserController
import ckan.lib.base as base
import ckan.model as model
import ckan.logic as logic
import ckan.logic.schema as schema
import ckan.lib.mailer as mailer
import ckan.lib.helpers as h
import logging
from ckan.common import _, c, request, response

abort = base.abort
render = base.render
log = logging.getLogger(__name__)

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
UsernamePasswordError = logic.UsernamePasswordError

class UserController(UserController):
    def _new_form_to_db_schema(self):
        from ckanext.datagovuk.schema import user_new_form_schema
        return user_new_form_schema()

    def _edit_form_to_db_schema(self):
        from ckanext.datagovuk.schema import user_edit_form_schema
        return user_edit_form_schema()

    def me(self, locale=None):
        if not c.user:
            h.redirect_to(locale=locale, controller='user', action='login',
                          id=None)
        user_ref = c.userobj.get_reference_preferred_for_uri()
        h.redirect_to(locale=locale, controller='user', action='dashboard_datasets')

    def _get_form_password(self):
        password1 = request.params.getone('password1')
        password2 = request.params.getone('password2')
        if (password1 is not None and password1 != ''):
            if not len(password1) >= 8:
                raise ValueError(_('Your password must be 8 '
                                 'characters or longer.'))
            elif not password1 == password2:
                raise ValueError(_('The passwords you entered'
                                 ' do not match.'))
            return password1
        raise ValueError(_('You must provide a password'))

    def request_reset(self):
        context = {'model': model, 'session': model.Session, 'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': request.params.get('user')}
        try:
            check_access('request_reset', context)
        except NotAuthorized:
            abort(403, _('Unauthorized to request reset password.'))

        if request.method == 'POST':
            id = request.params.get('user')

            context = {'model': model,
                       'user': c.user}

            data_dict = {'id': id}
            user_obj = None
            try:
                user_dict = get_action('user_show')(context, data_dict)
                user_obj = context['user_obj']
            except NotFound:
                # Try getting the user by email
                user_accounts = model.User.by_email(id)
                user_obj = user_accounts[0] if len(user_accounts) > 0 else None

                if not user_obj:
                    # Try searching the user
                    del data_dict['id']
                    data_dict['q'] = id

                    if id and len(id) > 2:
                        user_list = get_action('user_list')(context, data_dict)
                        if len(user_list) == 1:
                            del data_dict['q']
                            data_dict['id'] = user_list[0]['id']
                            user_dict = get_action('user_show')(context, data_dict)
                            user_obj = context['user_obj']
                        elif len(user_list) > 1:
                            h.flash_error(_('"%s" matched several users') % (id))
                        else:
                            h.flash_error(_('No such user: %s') % id)
                    else:
                        h.flash_error(_('No such user: %s') % id)

            if user_obj:
                try:
                    mailer.send_reset_link(user_obj)
                    h.flash_success(_('Please check your inbox for '
                                    'a reset code.'))
                    h.redirect_to('/')
                except mailer.MailerException, e:
                    h.flash_error(_('Could not send reset link: %s') %
                                  unicode(e))
        return render('user/request_reset.html')

    def user_list(self):
        print("index")
        log.debug('got index')
        import ckan.controllers.user.index as ckan_index
        context = {'model': model, 'session': model.Session, 'user': c.user,
                   'auth_user_obj': c.userobj}
        try:
            log.debug('check access')
            check_access('sysadmin', context)
        except NotAuthorized:
            abort(403, _('Not a sysadmin'))
        ckan_index()

