# -*- coding:utf8 -*-
from selenium import webdriver
from biz.mvnrepository import get_page_count, get_artifacts, set_artifact, search, get_version
from biz.orm import initial_database
from utils.common import ConfigUtil
from utils.log import getLogger

# 读取配置文件
config = ConfigUtil()


def main():

    driver = webdriver.Chrome()

    try:

        keyword = "spring"
        keyword = keyword.replace(' ', '+')
        url_list = []
        search_result = ''
        while search_result != 'success':
            search_result = search(driver, "spring")

        page_count = get_page_count(driver)
        url_list = get_artifacts(driver, page_count, keyword)
        if len(url_list):
            set_artifact(url_list)
        get_version(driver)

    finally:
        driver.quit()


if __name__ == '__main__':

    init_database_flag = config.load_value('system', 'init_database', 'False')
    if init_database_flag == 'True':
        initial_database()

    main()
