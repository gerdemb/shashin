import sqlite3
from pathlib import Path


class DB(object):
    def __init__(self, database_file):
        self._database_file = Path(database_file).expanduser()

    def __enter__(self):
        self._db_connection = sqlite3.connect(str(self._database_file))
        self._db_cur = self._db_connection.cursor()
        self._init_db()
        return self

    def __exit__(self, exc_class, exc, traceback):
        self._db_connection.commit()
        self._db_connection.close()

    def _execute(self, query, *params):
        return self._db_cur.execute(query, *params)

    def _commit(self):
        self._db_connection.commit()

    def _init_db(self):
        self._database_file.parent.mkdir(parents=True, exist_ok=True)
        self._db_cur.executescript(r'''
        CREATE TABLE IF NOT EXISTS images 
        (
            file_name TEXT PRIMARY KEY,
            mtime FLOAT NOT NULL,
            size INT NOT NULL,
            md5 BLOB NOT NULL,
            dhash BLOB
        );

        CREATE INDEX IF NOT EXISTS idx_md5 ON images 
        (
            md5
        );

        CREATE INDEX IF NOT EXISTS idx_dhash ON images 
        (
            dhash
        );


        ''')
        self._db_cur.row_factory = sqlite3.Row

    def image_insert(self, **kwargs):
        self._execute(r'''
            INSERT INTO images (file_name, mtime, size, md5, dhash) 
            VALUES (:file_name, :mtime, :size, :md5, :dhash)
        ''', kwargs)
        self._commit()

    def image_select_by_md5_and_size(self, md5, size):
        return self._execute(r'''
            SELECT * FROM images WHERE md5 = :md5 and size = :size
        ''', (md5, size))

    def image_select_by_dhash(self, dhash):
        return self._execute(r'''
            SELECT * FROM images WHERE dhash = ?
        ''', (dhash,))

    def image_select_by_file_name(self, file_name):
        return self._execute(r'''
            SELECT * FROM images WHERE file_name = ?
        ''', (file_name,)).fetchone()

    def image_select_all(self):
        return self._execute(r'''
            SELECT * FROM images
        ''')

    def image_select_random(self, num):
        return self._execute(r'''
            SELECT * FROM images ORDER BY RANDOM() LIMIT ?
        ''', (num,))

    def image_select_duplicate_dhash(self, start='', limit=10):
        return self._execute(r'''
            SELECT *
            FROM images
            INNER JOIN (
                SELECT dhash
                FROM images 
                WHERE dhash > ?
                GROUP BY dhash 
                HAVING count(dhash) > 1
                ORDER BY dhash
                LIMIT ?
                ) dups ON images.dhash = dups.dhash
            ORDER BY dhash;
        ''', (start, limit))

    def image_delete(self, file_name):
        self._execute(r'''
            DELETE FROM images WHERE file_name = ?
        ''', (file_name,))
        self._commit()

    def image_purge(self, condition):
        cursor2 = self._db_connection.cursor()
        for row in self._execute(r'''
                SELECT * FROM images
                '''):
            if condition(row):
                print("Missing {}".format(row['file_name']))
                cursor2.execute(r'''
                    DELETE FROM images WHERE file_name = ?
                ''', (row['file_name'],))
        self._commit()
