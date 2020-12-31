from pathlib import Path
import os

from db import DB
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
import base64
import json

class LabelImagesCommand(object):
    URL = 'https://vision.googleapis.com/v1/images:annotate'

    def __init__(self, config):
        self.database = config.database
        self.GOOGLE_APPLICATION_CREDENTIALS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    def execute(self):
        credentials = service_account.Credentials.from_service_account_file(self.GOOGLE_APPLICATION_CREDENTIALS)
        scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
        authed_session = AuthorizedSession(scoped_credentials)

        with DB(self.database) as db:
            for row in db.image_select_random_no_keywords(1):
                with open(row['file_name'], 'rb') as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode()
                    data = json.dumps(
                        {
                            "requests": [
                                {
                                "image": {
                                    "content": encoded_image
                                },
                                "features": [
                                    {
                                    "maxResults": 5,
                                    "type": "LABEL_DETECTION"
                                    }
                                ]
                                }
                            ]
                        }
                    )
                    response = authed_session.post(
                        self.URL,
                        data = data
                    )
                    print(row['file_name'], response.content)