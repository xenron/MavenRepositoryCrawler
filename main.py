# -*- coding:utf8 -*-
import sys

from selenium import webdriver

from biz.mvncompile import rewrite_xml, mvn_compile
from biz.mvnrepository import get_page_count, get_artifacts, set_artifact, search, get_version, search_by_group, \
    set_version, get_artifact_by_version_page
from biz.orm import initial_database, GroupArtifactVersion, Group
from biz.reload import load_group
from utils.common import ConfigUtil
from utils.log import getLogger

# 读取配置文件
config = ConfigUtil()


def search_group(driver):

    logger = getLogger()
    logger.info("method [search_group] start")

    try:
        group = Group.select().where(Group.proceed==False)
        if group:
            for item in group:
                search_by_group(driver, item.group)
                item.proceed = True
                item.save()
        else:
            logger.info('no group to search, program ends')

    finally:
        driver.quit()

    logger.info("method [search_group] end")


def search_version(driver):
    logger = getLogger()
    logger.info("method [search_version] start")

    try:
        get_version(driver)

    finally:
        driver.quit()

    logger.info("method [search_version] end")


def search_artifact_by_version(driver):
    logger = getLogger()
    logger.info("method [search_version] start")

    try:
        get_artifact_by_version_page(driver)

    finally:
        driver.quit()

    logger.info("method [search_version] end")


def maven_compile():
    logger = getLogger()
    logger.info("method [maven_compile] start")

    while True:
        query = GroupArtifactVersion.select().where(GroupArtifactVersion.proceed == False)
        if len(query):
            for item in query:
                rewrite_xml(item)
                result = mvn_compile()
                if result == 0:
                    logger.info('build {0}-{1}-{2} success, process next one'.format(
                        item.groupId, item.artifact, item.version))
                    item.proceed = True
                    item.save()
                else:
                    logger.info('build {0}-{1}-{2} success, process next one'.format(
                        item.groupId, item.artifact, item.version))
            break
        else:
            break

    logger.info("method [maven_compile] end")


def get_driver():

    logger = getLogger()
    logger.info("method [get_driver] start")

    driver_name = config.load_value('search', 'driver_name', 'firefox')
    logger.info('driver name is {0}'.format(driver_name))

    if driver_name == 'firefox':
        options = webdriver.FirefoxOptions()
        options.add_argument('-headless')
        profile = webdriver.FirefoxProfile()
        # 禁用图片
        profile.set_preference('permissions.default.image', 2)
        # 禁用flash（windows）
        profile.set_preference('dom.ipc.plugins.enabled.npswf32.dll', 'false')
        # 禁用flash（Linux）
        profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        driver = webdriver.Firefox(options=options, firefox_profile=profile)

    elif driver_name == 'chrome':
        options = webdriver.chrome.options.Options()
        options.add_argument('-headless')
        driver = webdriver.Chrome(options=options)

    logger.info("method [get_driver] end, driver is {0}".format(driver))
    return driver


if __name__ == '__main__':

    driver = get_driver()

    init_database_flag = config.load_value('system', 'init_database', 'False')
    if init_database_flag == 'True':
        initial_database()

    load_group('data/group.csv')

    if len(sys.argv) == 2:
        if sys.argv[1] == 'search_by_group':
            print('search_by_group')
            search_group(driver)
        elif sys.argv[1] == 'search_version':
            print('search_version')
            search_version(driver)
        elif sys.argv[1] == 'search_artifact_by_version':
            print('search_artifact_by_version')
            search_artifact_by_version(driver)
        elif sys.argv[1] == 'mvn_compile':
            print('mvn_compile')
            maven_compile()

