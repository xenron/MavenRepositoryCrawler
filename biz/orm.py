# -*- coding:utf8 -*-
from peewee import BooleanField, CharField, PrimaryKeyField
from utils.common import ConfigUtil
from utils.orm import BaseModel, database
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


class GroupIdArtifact(BaseModel):

    id = PrimaryKeyField()
    groupId = CharField(null=False)
    artifact = CharField(null=True)
    url = CharField(null=True, index=True)
    proceed = BooleanField(null=True)

    class Meta:
        order_by = ('id',)
        db_table = 'groupId_artifact'


class GroupIdArtifactVersion(BaseModel):

    id = PrimaryKeyField()
    groupId = CharField(null=False)
    artifact = CharField(null=True)
    version = CharField(null=True)
    url = CharField(null=True, index=True)
    proceed = BooleanField(null=True)

    class Meta:
        order_by = ('id',)
        db_table = 'groupId_artifact_version'


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

    database.drop_tables(
        [
            GroupIdArtifact,
            GroupIdArtifactVersion,
        ]
    )
    database.create_tables(
        [
            GroupIdArtifact,
            GroupIdArtifactVersion,
        ]
    )

    logger.info('method [initial_database] end')


if __name__ == '__main__':
    database.drop_tables(
        [
            GroupIdArtifactVersion,
        ]
    )



