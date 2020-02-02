# -*- coding:utf8 -*-
import os, pandas
from biz.orm import GroupId
from biz.orm import initial_database
from utils.common import ConfigUtil
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


'''
读取查询关键字信息
'''
def load_gradeId(file_path):

    logger = getLogger()
    logger.info('method [load_gradeId] start.')

    if os.path.exists(file_path) and os.path.isfile(file_path):

        df_state_time = pandas.read_excel(file_path, sheet_name=0, header=0)
        logger.info("input file [{0}], shape [{1}]".format(file_path, df_state_time.shape))

        for index, row in df_state_time.iterrows():

            groupId = row['groupId'].upper()

            if len(groupId):
                GroupId.create(
                    groupId=groupId,
                )
    else:
        logger.info("input file [{0}] not exists.".format(file_path))

    logger.info('method [load_gradeId] end')


if __name__ == '__main__':

    initial_database()
    load_gradeId('data/gradeId.xlsx')

