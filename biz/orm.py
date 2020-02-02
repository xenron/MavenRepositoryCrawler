# -*- coding:utf8 -*-
from peewee import BooleanField, CharField, PrimaryKeyField
from utils.common import ConfigUtil
from utils.orm import BaseModel, database
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


class GroupId(BaseModel):

    id = PrimaryKeyField()
    groupId = CharField(null=False)

    class Meta:
        order_by = ('id',)
        db_table = 'groupId'


class GroupIdArtifactVersion(BaseModel):

    id = PrimaryKeyField()
    groupId = CharField(null=False)
    artifact = CharField(null=True)
    version = CharField(null=True)
    proceed = BooleanField(null=True)

    class Meta:
        order_by = ('id',)
        db_table = 'groupId_artifact_version'


def initial_database():

    logger = getLogger('')
    logger.info('method [initial_database] start')

    database.drop_tables(
        [
            GroupId,
            GroupIdArtifactVersion,
        ]
    )
    database.create_tables(
        [
            GroupId,
            GroupIdArtifactVersion,
        ]
    )

    logger.info('method [initial_database] end')


if __name__ == '__main__':

    initial_database()



