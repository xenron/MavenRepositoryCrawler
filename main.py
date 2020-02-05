# -*- coding:utf8 -*-
import sys

from selenium import webdriver

from biz.mvncompile import rewrite_xml, mvn_compile
from biz.mvnrepository import get_page_count, get_artifacts, set_artifact, search, get_version, search_by_group, \
    set_version, get_artifact_by_version_page
from biz.orm import initial_database, GroupArtifactVersion
from utils.common import ConfigUtil
from utils.log import getLogger

# 读取配置文件
config = ConfigUtil()


def search_group():

    logger = getLogger()
    logger.info("method [search_group] start")
    driver = webdriver.Chrome()

    try:
        group = ["org.springframework", "org.springframework.boot"]
        for item in group:
            url_list = []
            url_list = search_by_group(driver, item)
            if len(url_list):
                set_artifact(url_list)

    finally:
        driver.quit()

    logger.info("method [search_group] end")


def search_version():
    logger = getLogger()
    logger.info("method [search_version] start")
    driver = webdriver.Chrome()

    try:
        get_version(driver)

    finally:
        driver.quit()

    logger.info("method [search_version] end")


def search_artifact_by_version():
    logger = getLogger()
    logger.info("method [search_version] start")
    driver = webdriver.Chrome()

    try:
        get_artifact_by_version_page(driver)

    finally:
        driver.quit()

    logger.info("method [search_version] end")


def maven_compile():
    logger = getLogger()
    logger.info("method [maven_compile] start")
    current_count = 1
    early_stop = False

    while True and (not early_stop):
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
                current_count += 1
                if current_count > 3:
                    early_stop = True
                    break
        else:
            break

    logger.info("method [maven_compile] end")


if __name__ == '__main__':

    init_database_flag = config.load_value('system', 'init_database', 'False')
    if init_database_flag == 'True':
        initial_database()

    if len(sys.argv) == 2:
        if sys.argv[1] == 'search_by_group':
            print('search_by_group')
            search_group()
        elif sys.argv[1] == 'search_version':
            print('search_version')
            search_version()
        elif sys.argv[1] == 'search_artifact_by_version':
            print('search_artifact_by_version')
            search_artifact_by_version()
        elif sys.argv[1] == 'mvn_compile':
            print('mvn_compile')
            maven_compile()

