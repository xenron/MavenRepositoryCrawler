# -*- coding:utf8 -*-
# -*- coding:utf8 -*-
import datetime

from peewee import MySQLDatabase, SqliteDatabase
from peewee import Model
from peewee import CharField, DateTimeField
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin
from utils.common import ConfigUtil
from utils.common import __singleton

# 读取配置文件
config = ConfigUtil()


class RetryMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
    _instance = None

    @staticmethod
    def get_db_instance():
        if not RetryMySQLDatabase._instance:
            RetryMySQLDatabase._instance = RetryMySQLDatabase(
                'mvnrepository',
                max_connections=8,
                stale_timeout=300,
                host='192.168.101.251',
                user='root',
                password='mysql',
                port=3306
            )

        return RetryMySQLDatabase._instance


@__singleton
class DatabaseUtil:

    def __init__(self):
        self.database = None
        self.database_type = config.load_value('system', 'database')
        if self.database_type == 'SQLite':
            # database = SqliteDatabase('./data/database.db', pragmas=[('journal_mode', 'wal')])
            self.database = SqliteDatabase('./data/database.db')
            # database = SqliteQueueDatabase('./data/database.db')
            # migrator = SqliteMigrator(database)
        elif self.database_type == 'MySQL':
            self.database = MySQLDatabase(
                database='mvnrepository',
                # database='tempdb',
                passwd='mysql',
                user='root',
                host='192.168.101.251',
                port=3306,
            )

    def get_database(self):
        return self.database

# database = SqliteDatabase('./data/database.db')
# migrator = SqliteMigrator(database)


class BaseModel(Model):
    # 创建时间
    create_datetime = DateTimeField(null=False, default=datetime.datetime.now)
    # 更新时间
    update_datetime = DateTimeField(null=True)
    # 备注说明
    description = CharField(null=True)

    class Meta:
        # database = database
        database = RetryMySQLDatabase.get_db_instance()


if __name__ == '__main__':

    pass



