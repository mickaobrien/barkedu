#!/usr/bin/env python

from exceptions import KeyError
import httplib2
import os

import oauth2client
from apiclient import discovery
from oauth2client import client, tools
import requests

#TODO move to config
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Bike Crashes'

#TODO this doesn't work with fab...
# try:
    # import argparse
    # flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
    # flags = None


class GoogleDoc(object):
    """
    A class for accessing a Google document as an object.
    Includes the bits necessary for accessing the document and auth and such.
    For example:

        doc = {
            "key": "123456abcdef",
            "file_name": "my_google_doc"
        }
        g = GoogleDoc(**doc)
        g.get_auth()
        g.get_document()

    Will download your google doc to data/file_name.format.
    """

    # You can update these values with kwargs.
    # In fact, you better pass a key or else it won't work!
    key = None
    file_format = 'xlsx'
    file_name = 'copy'
    gid = '0'

    # You can change these with kwargs but it's not recommended.
    spreadsheet_url = 'https://spreadsheets.google.com/feeds/download/spreadsheets/Export?key=%(key)s&exportFormat=%(format)s&gid=%(gid)s'
    new_spreadsheet_url = 'https://docs.google.com/spreadsheets/d/%(key)s/export?format=%(format)s&id=%(key)s&gid=%(gid)s'
    auth = None
    email = os.environ.get('APPS_GOOGLE_EMAIL', None)
    password = os.environ.get('APPS_GOOGLE_PASS', None)
    scope = "https://spreadsheets.google.com/feeds/"
    service = "wise"
    session = "1"

    def __init__(self, **kwargs):
        """
        Because sometimes, just sometimes, you need to update the class when you instantiate it.
        In this case, we need, minimally, a document key.
        """
        self.service = self._create_service()
        if kwargs:
            if kwargs.items():
                for key, value in kwargs.items():
                    setattr(self, key, value)

    def get_auth(self):
        """
        Gets an authorization token and adds it to the class.
        """
        data = {}
        if not self.email or not self.password:
            raise KeyError("Error! You're missing some variables. You need to export APPS_GOOGLE_EMAIL and APPS_GOOGLE_PASS.")

        else:
            data['Email'] = self.email
            data['Passwd'] = self.password
            data['scope'] = self.scope
            data['service'] = self.service
            data['session'] = self.session

            r = requests.post("https://www.google.com/accounts/ClientLogin", data=data)

            self.auth = r.content.split('\n')[2].split('Auth=')[1]

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'drive-quickstart.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatability with Python 2.6
                credentials = tools.run(flow, store)
            print '='*40
            print '  Storing credentials to ' + credential_path
            print '='*40
        return credentials

    def _create_service(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v2', http=http)
        return service

    def get_document(self):
        # Handle basically all the things that can go wrong.
        if not self.key:
            raise KeyError('Error! You forgot to pass a key to the class.')
        service = self.service
        url_params = { 'key': self.key, 'format': self.file_format, 'gid': self.gid }
        url = self.spreadsheet_url % url_params
        print 'Downloading {}'.format(url)
        resp, content = service._http.request(url)

        if resp.status != 200:
            resp, content = service._http.request(url)

        if resp.status != 200:
            raise Exception('No good')

        with open('data/%s.%s' % (self.file_name, self.file_format), 'wb') as writefile:
            writefile.write(content)
