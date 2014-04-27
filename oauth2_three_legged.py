from oauth2client.client import OAuth2WebServerFlow
from oauth2client.appengine import CredentialsProperty
from oauth2client.appengine import StorageByKeyName
import google_credentials
from google.appengine.api import users
from apiclient.discovery import build
from google.appengine.ext import db
import webapp2
import httplib2
import urllib
import pickle

CREDENTIALS_STORAGE_KEY = 'qvo-vadis'


class CredentialsModel(db.Model):
    credentials = CredentialsProperty()


class Oauth2_service():

    def __init__(self, api_client, version, scope):
        request = webapp2.get_request()
        cred = CredentialsModel.get_by_key_name(CREDENTIALS_STORAGE_KEY)
        if not cred:
            user = users.get_current_user()
            if not user:
                login_url = users.create_login_url(request.url)
                webapp2.redirect(login_url, abort=True)
            else:
                flow = OAuth2WebServerFlow(client_id=google_credentials.CLIENT_ID,
                                           client_secret=google_credentials.CLIENT_SECRET,
                                           scope=scope,
                                           redirect_uri=request.host_url + '/oauth2callback')
                state = {'original_url': request.url, 'scope': scope}
                state_string = pickle.dumps(state)
                auth_uri = flow.step1_get_authorize_url() + '&' + urllib.urlencode({'state': state_string})
                webapp2.redirect(auth_uri, abort=True)
        else:
            credentials = cred.credentials
            http = httplib2.Http()
            http = credentials.authorize(http)
            self.service = build(api_client, version, http=http)


class OauthHandler(webapp2.RequestHandler):

    def get(self):
        request = webapp2.get_request()
        code = request.get('code')
        state_string = request.get('state')
        state = pickle.loads(state_string)
        scope = state['scope']
        original_url = state['original_url']  # url of the original call
        flow = OAuth2WebServerFlow(client_id=google_credentials.CLIENT_ID,
                                   client_secret=google_credentials.CLIENT_SECRET,
                                   scope=scope,
                                   redirect_uri=request.path_url)
        credentials = flow.step2_exchange(code)
        user = users.get_current_user()
        storage = StorageByKeyName(CredentialsModel, CREDENTIALS_STORAGE_KEY, 'credentials')
        storage.put(credentials)
        return webapp2.redirect(original_url)
