from six import text_type

from ckan.common import g
from ckan.plugins.toolkit import redirect_to, abort
from ckan.views.user import (
    before_request,
    EditView,
    RegisterView,
)

from ckanext.datagovuk.schema import user_edit_form_schema


class _UserBeforeRequestMixin(object):
    """
    Use with MethodViews to ensure ckan.views.user.before_request is
    called before processing requests when view is not a member of the
    ckan.views.user.user blueprint to which it is normally applied.
    """
    def dispatch_request(self, *args, **kwargs):
        ret = before_request()
        return ret or super(_UserBeforeRequestMixin, self).dispatch_request(*args, **kwargs)


class DGUUserEditView(_UserBeforeRequestMixin, EditView):
    """
    An EditView that adds extra password policy policing
    """
    def _prepare(self, *args, **kwargs):
        context, id_ = super(DGUUserEditView, self)._prepare(*args, **kwargs)
        context[u"schema"] = user_edit_form_schema()
        return context, id_


class DGUUserRegisterView(_UserBeforeRequestMixin, RegisterView):
    """
    A RegisterView that disables the POST view
    """
    def post(self, *args, **kwargs):
        abort(403)


def me():
    """
    A slight variation on the default me() which prefers `dashboard.datasets`
    over `dashboard.index`
    """
    route = u'dashboard.datasets' if g.user else u'user.login'
    return redirect_to(route)
