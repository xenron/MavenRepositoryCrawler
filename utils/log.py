# -*- coding:utf-8 -*-
import logging, logging.config, sys, time


def __singletion(cls):
    """
    单例模式的装饰器函数
    :param cls: 实体类
    :return: 返回实体类对象
    """
    instances = {}
    def getInstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getInstance
 
 
@__singletion
class Log(object):

    def __init__(self):
        """
        获取日志处理对象
        :param appName: 应用程序名
        :param logFileName: 日志文件名
        :param out: 设置输出端：0：默认控制台，1：输入文件，其他：控制台和文件都输出
        :return: 返回日志对象
        """
        # self.appName = appName
        # self.logFileName = logFileName
        # self.out = out
        logging.config.fileConfig('logging.conf')
        self.logger_root = logging.getLogger()
        self.logger_custom = logging.getLogger('custom')
        time.sleep(2)

    def getRoot4Logger(self):
        return self.logger_root

    def getLogger4Custom(self):
        return self.logger_custom

    def getLogger1(self):
        # 获取logging实例
        logger = logging.getLogger(self.appName)
        # 指定输出的格式
        formatter = logging.Formatter('%(name)s  %(asctime)s  %(levelname)-8s:%(message)s')
 
        # 文件日志
        file_handler = logging.FileHandler(self.logFileName, encoding='utf-8')
        file_handler.setFormatter(formatter)
 
        # 控制台日志
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
 
        # # 指定日志的最低输出级别
        logger.setLevel(logging.INFO)  # 20
 
        # 为logger添加具体的日志处理器输出端
        if self.out == 1:
            logger.addHandler(file_handler)
        elif self.out == 0:
            logger.addHandler(console_handler)
        else:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        return logger

def getLogger(target=None):
    logger = None
    if target == 'custom':
        logger = Log().getLogger4Custom()
    elif target == '' or target == None:
        logger = Log().getRoot4Logger()
    return logger


# class Log(object):

#     def __init__(self, logger=None, log_cate='search'):

#         # Log设定
#         logging.config.fileConfig('logging.conf')
#         # 创建一个logger
#         self.logger = logging.getLogger(logger)


#     def getlog(self):

#         return self.logger


