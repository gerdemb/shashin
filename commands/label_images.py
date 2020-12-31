from pathlib import Path

from db import DB
from google.cloud import vision


class LabelImagesCommand(object):

    def __init__(self, config):
        self.database = config.database

    def execute(self):
        with DB(self.database) as db:
            for row in db.image_select_random_no_keywords(1):
                file = Path(row['file_name'])
                labels = self.detect_labels(file)
                print(labels)

    @staticmethod
    def detect_labels(path):
        """Detects labels in the file."""
        client = vision.ImageAnnotatorClient()

        with path.open('rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.label_detection(image=image)
        return response.label_annotations
        print('Labels:')

        for label in labels:
            print(label.description)

        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))
