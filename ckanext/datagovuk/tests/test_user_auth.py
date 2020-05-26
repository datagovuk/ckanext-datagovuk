"""Tests for user_auth API"""
from ckan import model, logic
from ckan.tests import factories, helpers
from ckanext.datagovuk.tests.db_test import DBTest


class TestUserAuth(DBTest):
    def setUp(self):
        super(self.__class__, self).setUp()

        sysadmin = factories.Sysadmin()
        self.context = {'model': model}

        self.user_dict = factories.User(email='hello@localhost')
        self.user = model.User.get(self.user_dict['id'])
        self.user.password = 'hello'
        self.user.save()

    def test_valid_call(self):
        resp = helpers.call_action(
            'user_auth',
            self.context,
            email=self.user.email,
            password='hello'
        )
        self.assertEqual(resp['email'], self.user.email)

    def test_missing_email(self):
        self.assertRaises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            email='',
            password='hello'
        )

    def test_missing_password(self):
        self.assertRaises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            email=self.user.email,
            password=''
        )

    def test_bad_email(self):
        self.assertRaises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            email='not-correct@localhost',
            password='hello'
        )

    def test_bad_password(self):
        self.assertRaises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            email=self.user.email,
            password='goodbye'
        )

    def test_bad_username_and_password(self):
        self.assertRaises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            email='wrong',
            password='password'
        )

    def test_user_list_authentication(self):
            self.assertRaises(
                logic.ValidationError,
                helpers.call_action,
                'user_list',
                self.context
            )

    def test_user_list_authorisation(self):
        self.assertRaises(
            logic.ValidationError,
            helpers.call_action,
            'user_list',
            self.context
        )