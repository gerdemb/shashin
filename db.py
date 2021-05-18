import sqlite3
from pathlib import Path
import json

class DB(object):
    def __init__(self, cache_dir):
        self._database_file = cache_dir / "shashin.sqlite3"

    def __enter__(self):
        self._db_connection = sqlite3.connect(str(self._database_file), timeout=30.0)
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
            dhash BLOB,
            metadata TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_dhash ON images 
        (
            dhash
        );

        CREATE TABLE IF NOT EXISTS ignore 
        (
            dhash BLOB PRIMARY KEY
        );

        ''')
        self._db_cur.row_factory = sqlite3.Row

    def image_insert_or_replace(self, **kwargs):
        kwargs['metadata'] = json.dumps(kwargs['metadata'])
        kwargs['file_name'] = str(kwargs['file_name'])
        self._execute(r'''
            INSERT OR REPLACE INTO images (file_name, mtime, size, dhash, metadata) 
            VALUES (:file_name, :mtime, :size, :dhash, :metadata)
        ''', kwargs)
        self._execute(r'''
            DELETE FROM ignore WHERE dhash = :dhash
        ''', kwargs)
        self._commit()

    def image_select_by_dhash(self, dhash):
        return self._execute(r'''
            SELECT * FROM images WHERE dhash = ?
        ''', (dhash,))

    def image_select_by_file_name(self, file_name):
        file_name = str(file_name)
        return self._execute(r'''
            SELECT * FROM images WHERE file_name = ?
        ''', (file_name,)).fetchone()

    def image_select_by_file_name_stats(self, file_name, mtime, size):
        file_name = str(file_name)
        return self._execute(r'''
            SELECT * 
            FROM images 
            WHERE file_name = :file_name AND mtime = :mtime AND size = :size
        ''', {
            'file_name': file_name,
            'mtime': mtime,
            'size': size,
        }).fetchone()

    def image_select_duplicate_dhash(self, start='', limit=10):
        return self._execute(r'''
            SELECT *
            FROM images
            INNER JOIN (
                SELECT dhash
                FROM images 
                WHERE 
                    dhash > ? AND
                    dhash NOT IN (SELECT dhash FROM ignore)
                GROUP BY dhash 
                HAVING count(dhash) > 1
                ORDER BY dhash
                LIMIT ?
                ) dups ON images.dhash = dups.dhash
            ORDER BY dhash;
        ''', (start, limit))

    def image_delete(self, file_name):
        file_name = str(file_name)
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
                cursor2.execute(r'''
                    DELETE FROM images WHERE file_name = ?
                ''', (row['file_name'],))
        self._commit()

    def ignore_insert_dhash(self, dhash):
        self._execute(r'''
            INSERT OR IGNORE INTO ignore (dhash) 
            VALUES (?)
        ''', (dhash,))
        self._commit()
