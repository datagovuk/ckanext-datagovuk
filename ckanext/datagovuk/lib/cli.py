import csv
import os
import subprocess
import sys
import sqlalchemy

from ckan import model
from ckan.common import config
from ckan.lib.cli import CkanCommand, query_yes_no
from ckan.lib.mailer import create_reset_key

from ckanext.harvest.harvesters.ckanharvester import CKANHarvester
from ckanext.harvest.logic.action.create import harvest_job_create, harvest_source_create
from ckanext.harvest.logic.schema import harvest_source_schema
from ckanext.harvest.model import define_harvester_tables
from ckanext.harvest.plugin import _create_harvest_source_object


class PasswordResetsCommand(CkanCommand):
    '''Resets the passwords of all users

     Resets the passwords of all users and generates a CSV
     containing a list of of email->resetkeys

        paster passwords_reset <output-filename>
    '''
    summary = __doc__.split('\n')[0]
    usage = '\n'.join(__doc__.split('\n')[1:])
    max_args = None
    min_args = 1

    def command(self):
        output_file = self.args[0]

        msg = "Are you sure you want to reset ALL of the user passwords?"

        confirm = query_yes_no(msg, default='no')
        if confirm == 'no':
            sys.stderr.write("Aborting...\n")
            sys.exit(1)

        self._load_config()
        import ckan.model as model
        import ckan.lib.search as search

        with open(output_file, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'email-address', 'reset-key'])

            for user in model.User.all():
                create_reset_key(user)
                user.save()

                writer.writerow([user.id, user.email, user.reset_key])


class CreateDGUTestDataCommand(CkanCommand):
    '''Creates the test data so that CKAN API functional tests can run

        Set your environment varibales:
            CKAN_INI - location of CKAN ini file 
            CKAN_TEST_SYSADMIN_NAME and CKAN_TEST_SYSADMIN_PASSWORD

        paster --plugin=ckanext-datagovuk create_dgu_test_data -c $CKAN_INI
    '''
    summary = __doc__.split('\n')[0]
    usage = '\n'.join(__doc__.split('\n')[1:])
    max_args = None
    min_args = None

    def add_empty_field(dataset_id, fieldname, model):
        field = model.PackageExtra(package_id=dataset_id, key=fieldname, value="")
        model.Session.add(field)

    def command(self):
        if not all(os.environ.get(i) for i in ('CKAN_TEST_SYSADMIN_NAME', 'CKAN_TEST_SYSADMIN_PASSWORD', 'CKAN_INI')):
            print('One of these env vars not set: CKAN_INI, CKAN_TEST_SYSADMIN_NAME or CKAN_TEST_SYSADMIN_PASSWORD')
            return

        print('====== Creating DGU test data')
        self._load_config()

        engine = sqlalchemy.create_engine(config.get('sqlalchemy.url'))
        model.init_model(engine)

        sysadmin_user = model.User.get(os.environ.get('CKAN_TEST_SYSADMIN_NAME'))
        if not sysadmin_user:
            print('=== Creating test sysadmin')
            sysadmin_user = model.User(
                name=os.environ.get('CKAN_TEST_SYSADMIN_NAME'),
                password=os.environ.get('CKAN_TEST_SYSADMIN_PASSWORD')
            )
            sysadmin_user.sysadmin = True
            model.Session.add(sysadmin_user)
            model.repo.commit_and_remove()

        publisher = model.Group.get('Example Publisher #1')
        if not publisher:
            print('=== Creating example publisher 1')
            model.Session.flush()
            # rev = model.repo.new_revision()
            # rev.author = u"DGU test admin"
            # rev.message = u"Creating Example Publisher #1."

            publisher = model.Group(
                name=u"example-publisher-1",
                title=u"Example Publisher #1",
                type=u"organization"
            )
            publisher.is_organization = True
            model.Session.add(publisher)
            model.repo.commit_and_remove()

            # rev = model.repo.new_revision()
            # rev.author = u"DGU test admin"
            # rev.message = u"Adding charity-ngo category for example publisher 1."

            category = model.GroupExtra(group_id=publisher.id, key="category", value="charity-ngo")
            model.Session.add(category)
            model.repo.commit_and_remove()

        if not model.Package.by_name(u"example-harvest-1"):
            print('=== Creating harvest source')

            version = ''
            if "ckan@db" in config.get('sqlalchemy.url'):
                if '5001' in config.get('ckan.site_url'):
                    version = '-2.8'
                elif '5002' in config.get('ckan.site_url'):
                    verions = '-2.9'

            source_dict = {
                'title': 'Example Harvest #1',
                'name': 'example-harvest-1',
                'url': "http://static-mock-harvest-source{}:11088/".format(version)\
                    if "ckan@db" in config.get('sqlalchemy.url') else \
                    "https://ckan-static-mock-harvest-source.cloudapps.digital/",
                'source_type': 'ckan',
                'owner_org': publisher.id,
                'notes': 'An example harvest source',
                'frequency': "MANUAL",
                'active': True,
                "config": None
            }
            context = {
                "model": model,
                "session": model.Session,
                "user": sysadmin_user.name,
                "ignore_auth": True,
                "schema": harvest_source_schema(),
                "message": "Create DGU example harvest source",
                "return_id_only": True
            }

            harvest_source_id = harvest_source_create(context, source_dict)

            if harvest_source_id:
                print("=== Creating harvest job")
                harvest_job_create(context, {"source_id": harvest_source_id, "run": False})

                print("=== Running harvest job")
                command = "paster --plugin=ckanext-harvest harvester run_test example-harvest-1 -c $CKAN_INI"
                run_command(command)

                model.Session.flush()

                print("=== Updating the example dataset to be in line with how DGU processes it")
                # rev = model.repo.new_revision()
                # rev.author = u"DGU test admin"
                # rev.message = u"Updating example-data-number-one for CKAN functional tests"

                dataset = model.Package.get("example-dataset-number-one")

                contact_name = model.PackageExtra(package_id=dataset.id, key="contact-name", value="Example User")
                model.Session.add(contact_name)

                empty_fields = [
                    "contact-email",
                    "contact-phone",
                    "schema-vocabulary",
                    "codelist",
                    "licence-custom",
                    "foi-web",
                    "foi-name",
                    "foi-email",
                    "foi-phone",
                    "theme-primary"
                ]

                for key in empty_fields:
                    field = model.PackageExtra(package_id=dataset.id, key=key, value="")
                    model.Session.add(field)

                delete_fields = [
                    "guid", "responsible-party", "taxonomy_url"
                ]
                for key in delete_fields:
                    field = model.Session.query(model.PackageExtra).filter(
                        model.PackageExtra.package_id == dataset.id, model.PackageExtra.key == key
                    ).first()
                    if field:
                        field.delete()

                model.repo.commit_and_remove()

                print("=== Running search index rebuild")
                command = 'ckan search-index rebuild %s -c $CKAN_INI' % dataset.name
                run_command(command)

        publisher2 = model.Group.get('Example Publisher #2')
        if not publisher2:
            print('=== Creating example publisher 2')
            model.Session.flush()
            # rev = model.repo.new_revision()
            # rev.author = u"DGU test admin"
            # rev.message = u'''Creating Example Publisher #2.'''

            publisher2 = model.Group(
                name=u"example-publisher-2",
                title=u"Example Publisher #2",
                type="organization"
            )
            publisher2.is_organization = True
            model.Session.add(publisher2)
            model.repo.commit_and_remove()

        print("=== To use with CKAN functional tests in ckan-vars.conf set OWNER_ORG=%s" % publisher.id)
        print("====== DGU test data created")


class RemoveDGUTestDataCommand(CkanCommand):
    '''Removes the DGU test data

        Set your environment varibales:
            CKAN_INI - location of CKAN ini file 
            CKAN_TEST_SYSADMIN_NAME

        paster --plugin=ckanext-datagovuk remove_dgu_test_data -c $CKAN_INI
    '''
    summary = __doc__.split('\n')[0]
    usage = '\n'.join(__doc__.split('\n')[1:])
    max_args = None
    min_args = None

    def command(self):
        if not all(os.environ.get(i) for i in ('CKAN_TEST_SYSADMIN_NAME', 'CKAN_INI')):
            print('CKAN_TEST_SYSADMIN_NAME or CKAN_INI env var not set')
            return

        print('====== Removing DGU test data')
        self._load_config()

        engine = sqlalchemy.create_engine(config.get('sqlalchemy.url'))
        model.init_model(engine)

        command = "paster --plugin=ckanext-harvest harvester clearsource example-harvest-1 -c $CKAN_INI"
        run_command(command)

        command = "paster --plugin=ckanext-harvest harvester rmsource example-harvest-1 -c $CKAN_INI"
        run_command(command)

        sql = '''
        DELETE FROM package_extra_revision WHERE package_id in (SELECT id FROM package WHERE name='example-harvest-1'); 
        DELETE FROM package_extra WHERE package_id IN (SELECT id FROM package WHERE name='example-harvest-1');
        DELETE FROM package_revision WHERE name = 'example-harvest-1';
        DELETE FROM package WHERE name = 'example-harvest-1';
        DELETE FROM harvest_object WHERE harvest_source_id IN (SELECT id FROM harvest_source WHERE title = 'Example Harvest #1');
        DELETE FROM harvest_job WHERE source_id IN (SELECT id FROM harvest_source WHERE title = 'Example Harvest #1');
        DELETE FROM harvest_source WHERE title = 'Example Harvest #1';
        DELETE FROM member_revision WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
        DELETE FROM member WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
        DELETE FROM group_extra_revision WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
        DELETE FROM group_extra WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
        DELETE FROM group_revision WHERE name = 'example-publisher-1';
        DELETE FROM "group" WHERE name = 'example-publisher-1';
        DELETE FROM group_revision WHERE name = 'example-publisher-2';
        DELETE FROM "group" WHERE name = 'example-publisher-2';
        DELETE FROM "user" WHERE name = :testadmin_name;
        '''

        model.Session.execute(sql, {"testadmin_name": os.environ.get('CKAN_TEST_SYSADMIN_NAME')})
        model.repo.commit_and_remove()

        command = 'ckan search-index clear example-publisher-1 -c $CKAN_INI'
        run_command(command)

        command = 'ckan search-index clear example-publisher-2 -c $CKAN_INI'
        run_command(command)

        print("====== DGU test data removed")

def run_command(command):
    try:
        print("=== Running %s" % command)
        subprocess.check_call(command, shell=True)
    except Exception as exception:
        print("=== Error: %s" % exception)
