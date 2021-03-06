# -*- coding:utf8 -*-
import os, pandas
from biz.orm import Group
from biz.orm import initial_database
from utils.common import ConfigUtil
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


'''
读取查询关键字信息
'''
def load_group(file_path):

    logger = getLogger()
    logger.info('method [load_group] start.')

    if os.path.exists(file_path) and os.path.isfile(file_path):

        group_info = pandas.read_csv(file_path, header=0)
        logger.info("input file [{0}], shape [{1}]".format(file_path, group_info.shape))

        for index, row in group_info.iterrows():

            group = row['group']

            if len(group):
                query = Group.select().where(Group.group == group)
                if query:
                    continue
                else:
                    Group.create(
                        group=group,
                        proceed=False,
                    )
    else:
        logger.info("input file [{0}] not exists.".format(file_path))

    logger.info('method [load_group] end')


if __name__ == '__main__':

    # initial_database()
    load_group('data/group.csv')

