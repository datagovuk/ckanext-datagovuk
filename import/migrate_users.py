'''
Migrates the DGU user info from the old DGU-customized CKAN to be
suitable for loading into a vanilla CKAN.
'''
import argparse
import json
import os
import gzip
import csv
import datetime
import random
import string

from running_stats import Stats

args = None
stats = Stats()

def process():
    # read drupal users
    with gzip.open(args.drupal_users_table_fpath, 'rb') as csv_read_file:
        csv_reader = csv.DictReader(csv_read_file)
        drupal_users = dict(
            (user_dict['uid'], user_dict)
            for user_dict in csv_reader
            )

    ckan_users_in_organisations = {}
    with gzip.open(args.ckan_organisation_fpath, 'rb') as ckan_organisation_f:
        lines = ckan_organisation_f.readlines()
        for line in lines:
           organisation = json.loads(line)
           if 'users' in organisation:
              for user in organisation['users']:
                  ckan_users_in_organisations[user['name']] = 1

    with gzip.open(args.ckan_users_fpath, 'rb') as ckan_users_f, \
            gzip.open(args.output_fpath_discarded, 'wb') as output_f_discarded, \
            gzip.open(args.output_fpath, 'wb') as output_f:


        # migrate ckan users
        drupal_ids_written = set()
        lines = ckan_users_f.readlines()
        ckan_user_map = {}
        for line in lines:
            user, drupal_id, old_user_name = migrate_ckan_user(line, drupal_users)
            ckan_user_map[old_user_name] = user['name'] # create a dictionary for mapping old user names to new user names
            if old_user_name in ckan_users_in_organisations:
                output_f.write(json.dumps(user) + '\n')
                if drupal_id is not None:
                    stats.add('Migrated CKAN-Drupal user', drupal_id)
                    drupal_ids_written.add(drupal_id)
                else:
                    stats.add('Migrated pure CKAN user', user['name'])
            else:
                stats.add('CKAN user not found in organisation', user['name'])
                if 'email' in user and user['email'] is not None:
                    output_f_discarded.write(user['email'] + '\n')

        # migrate drupal-only users
        drupal_only_users = sorted(list(
            set(drupal_users.keys()) - drupal_ids_written))
        for drupal_id in drupal_only_users:
            drupal_user = drupal_users[drupal_id]
            user, drupal_id, old_user_name = drupal_to_ckan_user(drupal_user)
            ckan_user_map[old_user_name] = user['name']
            if old_user_name in ckan_users_in_organisations:
                output_f.write(json.dumps(user) + '\n')
                stats.add('Migrated pure Drupal user', drupal_id)

    # update the user identifiers in the organisations file
    with gzip.open(args.ckan_organisation_fpath, 'rb') as ckan_organisation_f, \
            gzip.open(args.output_organisation_fpath, 'wb') as output_f:
        lines = ckan_organisation_f.readlines()
        for line in lines:
            organisation = migrate_ckan_organisation(line, ckan_user_map)
            output_f.write(json.dumps(organisation) + '\n')

    print stats
    print 'Written %s' % args.output_fpath

def migrate_ckan_organisation(ckan_organisation_json, ckan_user_map):
    organisation = json.loads(ckan_organisation_json)
    
    # get the users and update their name 
    for user in organisation['users']:
      if user['name'] in ckan_user_map:
          user['name'] = ckan_user_map[user['name']]
      else:
          print stats.add('No mapping found for organisation user', user['name'])

    # promote some of the extras to schema fields
    keys = ['contact-name', 'contact-email', 'contact-phone', 'foi-name', 'foi-email', 'foi-web', 'foi-phone']
    for key in keys:
        for extra in organisation['extras']:
            if extra['key'] == key:
                organisation[key] = extra['value']
                organisation['extras'].remove(extra)
 
    return organisation

def migrate_ckan_user(ckan_user_json, drupal_users):
    user = json.loads(ckan_user_json)

    old_user_name = user['name']

    # password comes from Drupal
    if user['name'].startswith('user_d'):
        drupal_id = user['name'].replace('user_d', '')
        if 'activity' in user:
            for activity in user['activity']:
              activity['author'] = user['name']
        drupal_user = drupal_users.get(drupal_id)
        if not drupal_user:
            print stats.add('Cannot find drupal equivalent to ckan user',
                            drupal_id)
        else:
            # replace ckan password with the drupal one (in production mode only)
            user['password_hash'] = drupal_user['pass'] if args.production else random_password_hash(50)
    else:
        # password is left as the ckan one - assuming we have PR merged:
        # https://github.com/datagovuk/ckan/pull/26
        drupal_id = None
        user['password_hash'] = drupal_user['pass'] if args.production else random_password_hash(50)

    return user, drupal_id, old_user_name

def drupal_to_ckan_user(drupal_user):
    created = datetime.datetime.fromtimestamp(int(drupal_user['created']))
    old_user_name = drupal_user['name']
    user = dict(
        name=drupal_user['mail'],
        fullname=drupal_user['name'],
        email=drupal_user['mail'],
        password_hash=drupal_user['pass'] if args.production else random_password_hash(50),
        sysadmin=False,  # TODO
        about='User account %s imported from Drupal system' % drupal_user['uid'],
        created=created.strftime('%Y-%m-%dT%H:%M:%S'),  # 2011-07-18T11:44:28
        activity_streams_email_notifications=False,
        state='active',
        )
    return user, drupal_user['uid'], old_user_name

def random_password_hash(length):
    return ''.join((random.choice(string.letters + string.digits + string.punctuation)) for x in range(length))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ckan_users_fpath',
                        help='Specify the location of the (old) CKAN users jsonl.gz file')
    parser.add_argument('drupal_users_table_fpath',
                        help='Specify the location of the Drupal users table csv.gz file')
    parser.add_argument('output_fpath',
                        help='Specify the location of the user output file')
    parser.add_argument('output_fpath_discarded',
                        help='Specify the location of the discarded user output file')
    parser.add_argument('ckan_organisation_fpath',
                        help='Specify the location of the organisation file')
    parser.add_argument('output_organisation_fpath',
                        help='Specify the location of the organisation output file')
    parser.add_argument('--production',
                        help='Specify to import password hashes from Drupal, else random strings are generated as passwords',
                        action="store_true")

    args = parser.parse_args()
    for fpath in (args.ckan_users_fpath, args.drupal_users_table_fpath, args.ckan_organisation_fpath):
        if not os.path.exists(args.ckan_users_fpath):
            args.error('Source file {} could not be found' % fpath)

    process()
