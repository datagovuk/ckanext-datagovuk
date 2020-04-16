import logging
from pylons import config

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan import model
from ckan.lib.plugins import DefaultTranslation
from ckan.config.routing import SubMapper

import ckanext.datagovuk.auth as auth
import ckanext.datagovuk.schema as schema_defs
import ckanext.datagovuk.action.create
import ckanext.datagovuk.action.get
import ckanext.datagovuk.action.update
import ckanext.datagovuk.upload as upload

from ckanext.datagovuk.logic.theme_validator import valid_theme
from ckanext.harvest.model import HarvestSource, HarvestJob, HarvestObject

from pylons.wsgiapp import PylonsApp

from flask import Blueprint

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware


class DatagovukPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public', 'public')
        toolkit.add_resource('fanstatic/vendor', 'vendor')

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'group_create': auth.group_create,
            'organization_create': auth.organization_create,
            'user_auth': auth.user_auth
        }

    # IDatasetForm

    def _modify_package_schema(self, schema):
        schema.update({
            'theme-primary': [toolkit.get_validator('ignore_missing'),
                              toolkit.get_validator('valid_theme'),
                              toolkit.get_converter('convert_to_extras')],
            'licence-custom': [toolkit.get_validator('ignore_missing'),
                              toolkit.get_converter('convert_to_extras')],
            'schema-vocabulary': [toolkit.get_validator('ignore_missing'),
                                  toolkit.get_converter('convert_to_extras')],
            'codelist': [toolkit.get_validator('ignore_missing'),
                         toolkit.get_converter('convert_to_extras')],
            'author_email': [toolkit.get_validator('ignore_missing'),
                             unicode],
            'maintainer_email': [toolkit.get_validator('ignore_missing'),
                             unicode],
        })
        for contact_key in ['contact-name', 'contact-email', 'contact-phone', 'foi-name', 'foi-email', 'foi-web', 'foi-phone']:
            schema.update({
                contact_key: [toolkit.get_validator('ignore_missing'),
                              toolkit.get_converter('convert_to_extras')]
            })

        from ckan.logic.schema import default_extras_schema
        from ckan.lib.navl.validators import ignore, not_empty
        from ckanext.datagovuk.logic.validators import extra_key_not_in_root_schema

        extras_schema = default_extras_schema()
        extras_schema['key'] = [
            not_empty,
            extra_key_not_in_root_schema,
            unicode,
        ]

        schema['extras'] = extras_schema

        schema['resources'].update({
            'resource-type': [toolkit.get_validator('ignore_missing')],
            'datafile-date': [toolkit.get_validator('ignore_missing')],
        })

        # was expecting:
        #   schema['harvest'] = [ignore]
        # to work but it doesn't prevent `harvest` from being added to
        # `__junk` which will cause updates on datasets to fail
        # See the issue on CKAN - https://github.com/ckan/ckan/issues/4989
        # as there may be better ways to resolve this issue
        schema['harvest'] = {'_': ignore}

        return schema

    def create_package_schema(self):
        from ckan.logic.schema import default_create_package_schema
        schema = schema_defs.create_package_schema(default_create_package_schema())
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        from ckan.logic.schema import default_update_package_schema
        schema = schema_defs.update_package_schema(default_update_package_schema())
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        from ckan.logic.schema import default_show_package_schema
        schema = schema_defs.show_package_schema(default_show_package_schema())
        schema.update({
            'theme-primary': [toolkit.get_converter('convert_from_extras'),
                              toolkit.get_validator('ignore_missing')],
            'licence-custom': [toolkit.get_converter('convert_from_extras'),
                               toolkit.get_validator('ignore_missing')],
            'schema-vocabulary': [toolkit.get_converter('convert_from_extras'),
                                  toolkit.get_validator('ignore_missing')],
            'codelist': [toolkit.get_converter('convert_from_extras'),
                         toolkit.get_validator('ignore_missing')],
        })
        for contact_key in ['contact-name', 'contact-email', 'contact-phone', 'foi-name', 'foi-email', 'foi-web', 'foi-phone']:
            schema.update({
                contact_key: [toolkit.get_converter('convert_from_extras'),
                              toolkit.get_validator('ignore_missing')]
            })
        schema['resources'].update({
                'resource-type' : [toolkit.get_validator('ignore_missing')],
                'datafile-date' : [toolkit.get_validator('ignore_missing')]
            })
        return schema

    def is_fallback(self):
        # This is the default dataset form
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # IPackageController

    def before_index(self, data_dict):
        return schema_defs.trim_strings_for_index(data_dict)

    def after_show(self, context, data_dict):
        if 'type' in data_dict and data_dict['type'] != 'harvest':
            harvest_object = model.Session.query(HarvestObject) \
                    .filter(HarvestObject.package_id==data_dict['id']) \
                    .filter(HarvestObject.current==True) \
                    .first()

            if harvest_object:
                data_dict['harvest'] = []
                for key, value in [
                    ('harvest_object_id', harvest_object.id),
                    ('harvest_source_id', harvest_object.source.id),
                    ('harvest_source_title', harvest_object.source.title),
                        ]:
                    data_dict['harvest'].append({'key': key, 'value': value})

        return data_dict

    # IActions

    def get_actions(self):
        return dict(
            organization_show=ckanext.datagovuk.action.get.dgu_organization_show,
            package_search=ckanext.datagovuk.action.get.dgu_package_search,
            package_show=ckanext.datagovuk.action.get.dgu_package_show,
            resource_create=ckanext.datagovuk.action.create.resource_create,
            user_auth=ckanext.datagovuk.action.get.user_auth,
            user_create=ckanext.datagovuk.action.create.user_create,
            user_update=ckanext.datagovuk.action.update.dgu_user_update,
        )

    # IValidators

    def get_validators(self):
        from ckanext.datagovuk.logic.user_email_validator import correct_email_suffix
        from ckanext.datagovuk.logic.validators import user_password_validator
        return {
            'correct_email_suffix': correct_email_suffix,
            'valid_theme': valid_theme,
            'user_password_validator_dgu': user_password_validator,
        }

    # IBlueprint

    def get_blueprint(self):
        from ckanext.datagovuk.views.healthcheck import healthcheck
        from ckanext.datagovuk.views.accessibility import accessibility
        from ckanext.datagovuk.views.user import (
            DGUUserEditView,
            DGUUserRegisterView,
            DGUUserRequestResetView,
            me,
        )
        bp = Blueprint("datagovuk", self.__module__)

        bp.add_url_rule(u"/healthcheck", view_func=healthcheck)
        bp.add_url_rule(u"/accessibility", view_func=accessibility)

        bp.add_url_rule(
            u"/user/register",
            view_func=DGUUserRegisterView.as_view(str(u'register')),
        )

        _user_edit_view = DGUUserEditView.as_view(str(u'edit'))
        bp.add_url_rule(u'/user/edit', view_func=_user_edit_view)
        bp.add_url_rule(u'/user/edit/<id>', view_func=_user_edit_view)

        bp.add_url_rule(u'/user/me', view_func=me)
        # also monkeypatch occurrence in original module as some views
        # call it directly instead of redirecting externally
        import ckan.views.user as ckan_user_views
        ckan_user_views.me = me

        bp.add_url_rule(
            u'/user/reset',
            view_func=DGUUserRequestResetView.as_view(str(u'request_reset')),
        )

        return bp

    # IRoutes

    def before_map(self, route_map):
        # user_controller = 'ckanext.datagovuk.controllers.user:UserController'
        healthcheck_controller = 'ckanext.datagovuk.controllers.healthcheck:HealthcheckController'
        api_search_dataset_controller = 'ckanext.datagovuk.controllers.api:DGUApiController'
        # with SubMapper(route_map, controller=user_controller) as m:
        #     m.connect('register', '/user/register', action='register')
        #     m.connect('/user/logged_in', action='logged_in')
        #     m.connect('/user/edit', action='edit')
        #     m.connect('/user/edit/{id:.*}', action='edit')
        #     m.connect('/user/reset', action='request_reset')
        route_map.connect('healthcheck', '/healthcheck', controller=healthcheck_controller, action='healthcheck')
        route_map.connect('/api/search/dataset', controller=api_search_dataset_controller, action='api_search_dataset')
        route_map.connect('/api/3/search/dataset', controller=api_search_dataset_controller, action='api_search_dataset')
        route_map.redirect('/home', '/')
        return route_map

    def after_map(self, route_map):
        # Deletes all the organization routes
        delete_routes_by_path_startswith(route_map, '/organization')

        harvest_org_controller = 'ckanext.harvest.controllers.organization:OrganizationController'
        route_map.connect('harvest_org_list', '/publisher/harvest/' + '{id}', controller=harvest_org_controller, action='source_list')

        # add this function in OrganizationController as CKAN doesn't have 'publisher' group type
        def _guess_group_type(self, expecting_name=False):
            return 'organization'
        
        from ckan.controllers.organization import OrganizationController
        OrganizationController._guess_group_type = _guess_group_type

        # Recreates the organization routes with /publisher instead.
        with SubMapper(route_map, controller='organization') as m:
            m.connect('organizations_index', '/publisher', action='index')
            m.connect('organization_index', '/publisher', action='index')
            m.connect('organization_new', '/publisher/new', action='new')
            for action in [
            'delete',
            'admins',
            'member_new',
            'member_delete',
            'history']:
                m.connect('organization_' + action,
                        '/publisher/' + action + '/{id}',
                        action=action)

            m.connect('organization_activity', '/publisher/activity/{id}/{offset}',
                    action='activity')
            m.connect('organization_read', '/publisher/{id}', action='read')
            m.connect('organization_about', '/publisher/about/{id}',
                    action='about')
            m.connect('organization_read', '/publisher/{id}', action='read',
                    ckan_icon='sitemap')
            m.connect('organization_edit', '/publisher/edit/{id}',
                    action='edit')
            m.connect('organization_members', '/publisher/members/{id}',
                    action='members')
            m.connect('organization_bulk_process',
                    '/publisher/bulk_process/{id}',
                    action='bulk_process')

        route_map.connect('harvest_index', '/harvest', action='index')

        return route_map

    # ITemplateHelpers

    def get_helpers(self):
        import ckanext.datagovuk.helpers as h
        return {
            'themes': h.themes,
            'activate_upload': h.activate_upload,
            'schemas': h.schemas,
            'split_values': h.split_values,
            'codelist': h.codelist,
            'alphabetise_dict': h.alphabetise_dict,
            'roles': h.roles,
            'google_analytics_tracking_id': h.google_analytics_tracking_id,
            'publisher_category': h.publisher_category,
            'is_central_gov_organogram': h.is_central_gov_organogram,
        }

    # IMiddleware

    def before_send(self, event, hint):
        return None if [i for i in ['localhost', 'integration', 'staging'] if i in config.get('ckan.site_url')] \
            else event

    def make_middleware(self, app, config):
        # we get this called twice, once for Flask and once for Pylons
        if isinstance(app, PylonsApp):
            return SentryWsgiMiddleware(app)
        else:
            sentry_sdk.init(before_send=self.before_send, integrations=[FlaskIntegration()])
            return app

    # IResourceController

    def before_create_or_update(self, context, resource):
        """before_create_or_update - our own function. NOT a CKAN hook.
        Contains shared code performed regardless of whether we are
        creating or updating.
        """

        # If resource is an API, don't do anything special
        if resource.get("format") == "API":
            return
        elif resource.get("upload") is None:
            return
        elif not upload.config_exists():
            logger = logging.getLogger(__name__)
            logger.error(
                "Required S3 config options missing. Please check if required config options exist."
            )
            raise KeyError("Required S3 config options missing")

    def before_create(self, context, resource):
        """Runs before resource_create. Modifies resource destructively to put in the S3 URL"""
        self.before_create_or_update(context, resource)

    def before_update(self, context, _, resource):
        """Runs before resource_update. Modifies resource destructively to put in the S3 URL"""
        self.before_create_or_update(context, resource)

    import ckanext.datagovuk.ckan_patches  # import does the monkey patching


def delete_routes_by_path_startswith(map, path_startswith):
    """
    This function will remove from the routing map any
    path that starts with the provided argument (/ required).

    Not really a great thing to be doing, but CKAN doesn't
    provide a way to i18n URLs because it'll likely cause
    clashes with other group subclasses.
    """
    matches_to_delete = []
    for match in map.matchlist:
        if match.routepath.startswith(path_startswith):
            matches_to_delete.append(match)
    for match in matches_to_delete:
        map.matchlist.remove(match)
