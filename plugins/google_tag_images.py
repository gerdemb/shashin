from pathlib import Path
from synology import get_thumbnail
from plugins import Plugin
from google.cloud import vision
import io

from exif import Exif

class GoogleTagImages(Plugin):
    def __init__(self, config):
        super().__init__(
            config,
            r'''SELECT * FROM images WHERE json_extract(metadata, '$.Keywords') is NULL ORDER BY RANDOM() LIMIT ?''',
            (config.number,)
        )

    def process_row(self, et: Exif, row):
        client = vision.ImageAnnotatorClient()
    
        file_name = Path(row['file_name'])

        # Sanity check that Keywords have not been set
        metadata = et.get_metadata(file_name)
        if 'Keywords' not in metadata:
            thumbnail = get_thumbnail(file_name, size='XL')
            if thumbnail.exists():
                with io.open(thumbnail, 'rb') as image_file:
                    content = image_file.read()
                image = vision.Image(content=content)

                response = client.label_detection(image=image)
                labels = response.label_annotations

                # params = [
                #     f'-Keywords={l}'
                #     for l in labels
                # ]
                # result = et.execute_raw(
                #     file_name,
                #     *params
                # )
                print(file_name, labels)