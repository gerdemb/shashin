from db import DB
from exif import Exif


class Plugin(object):

    def __init__(self, config, sql_select, sql_params):
        self.cache_dir = config.cache_dir
        self.sql_select = sql_select
        self.sql_params = sql_params

    def execute(self):
        with DB(self.cache_dir) as db:
            with Exif() as et:
                for row in db._execute(self.sql_select, self.sql_params):
                    self.process_row(et, row)

    def process_row(self, et, row):
        raise NotImplementedError