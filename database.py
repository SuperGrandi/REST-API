import pymysql


class Database:
    def __init__(self):
        self.db = pymysql.connect(
            host="coco-db.c9qa2gunxiki.ap-northeast-2.rds.amazonaws.com",
            user='admin',
            password='KthRTVxfhLIi4t9LRcVI',
            db='coco_db',
            charset='utf8'
        )
        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)

    def execute(self, query, args=None):
        if args is None:
            args = {}
        self.cursor.execute(query, args)

    def executeOne(self, query, args=None):
        if args is None:
            args = {}
        self.cursor.execute(query, args)
        row = self.cursor.fetchone()
        return row

    def executeAll(self, query, args=None):
        if args is None:
            args = {}
        self.cursor.execute(query, args)
        row = self.cursor.fetchall()
        return row

    def commit(self):
        self.db.commit()
