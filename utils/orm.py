# -*- coding:utf8 -*-
from peewee import MySQLDatabase, SqliteDatabase
from peewee import Model
from peewee import CharField, DateTimeField
from playhouse.migrate import SqliteMigrator, migrate
import datetime

database = SqliteDatabase('./data/database.db')
migrator = SqliteMigrator(database)


class BaseModel(Model):
    # 创建时间
    create_datetime = DateTimeField(null=False, default=datetime.datetime.now)
    # 更新时间
    update_datetime = DateTimeField(null=True)
    # 备注说明
    description = CharField(null=True)

    class Meta:
        database = database


if __name__ == '__main__':

    pass



