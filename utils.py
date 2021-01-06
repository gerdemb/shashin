import hashlib
import sqlite3

import dhash
from send2trash import send2trash
from wand.exceptions import MissingDelegateError, DelegateError
from wand.image import Image




def delete_image(db, file_name):
    db.image_delete(str(file_name))
    send2trash(str(file_name))