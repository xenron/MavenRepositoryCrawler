# -*- coding:utf8 -*-
from peewee import BooleanField, CharField, PrimaryKeyField
from utils.common import ConfigUtil
from utils.orm import BaseModel, DatabaseUtil
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


class Group(BaseModel):

    id = PrimaryKeyField()
    group = CharField(null=False)
    proceed = BooleanField(null=True)

    class Meta:
        order_by = ('id',)
        db_table = 'group_info'


class GroupIdArtifact(BaseModel):

    id = PrimaryKeyField()
    groupId = CharField(null=False)
    artifact = CharField(null=True)
    url = CharField(null=True, index=True)
    proceed = BooleanField(null=True)

    class Meta:
        order_by = ('id',)
        db_table = 'group_artifact'


class GroupArtifactVersion(BaseModel):

    id = PrimaryKeyField()
    groupId = CharField(null=False)
    artifact = CharField(null=True)
    version = CharField(null=True)
    url = CharField(null=True, index=True)
    searched = BooleanField(null=True, default=False)
    proceed = BooleanField(null=True, default=False)

    class Meta:
        order_by = ('id',)
        db_table = 'group_artifact_version'


def initial_database():

    logger = getLogger('')
    logger.info('method [initial_database] start')

    DatabaseUtil().get_database().drop_tables(
        [
            Group,
            GroupIdArtifact,
            GroupArtifactVersion,
        ]
    )
    DatabaseUtil().get_database().create_tables(
        [
            Group,
            GroupIdArtifact,
            GroupArtifactVersion,
        ]
    )

    logger.info('method [initial_database] end')


if __name__ == '__main__':

    initial_database()




