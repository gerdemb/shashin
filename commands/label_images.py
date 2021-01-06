from pathlib import Path
import os
from shashin import GOOGLE_APPLICATION_CREDENTIALS

from db import DB
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
import base64
import json
from exif import Exif

class LabelImagesCommand(object):
    URL = 'https://vision.googleapis.com/v1/images:annotate'

    def __init__(self, config):
        self.database = config.database

    def execute(self):
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
        scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
        authed_session = AuthorizedSession(scoped_credentials)

        with DB(self.database) as db:
            with Exif() as et:
                for row in db.image_select_random_no_keywords(10):
                    file_name = row['file_name']
                    with open(file_name, 'rb') as image_file:
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
                        content = json.loads(response.content)
                        labels = [
                            l['description']
                            for l in content['responses'][0]['labelAnnotations']
                        ]
                        params = [
                            f'-Keywords={l}'
                            for l in labels
                        ]
                        result = et.execute_raw(
                            file_name,
                            *params
                        )
                        print(file_name, labels, result.strip())
