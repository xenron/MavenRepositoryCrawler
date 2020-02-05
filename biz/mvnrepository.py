# -*- coding:utf8 -*-
import math

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import datetime, random, time, traceback

from biz.orm import GroupIdArtifact, GroupArtifactVersion
from utils.common import ConfigUtil
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


# 按页查询group artifact信息，返回url list
def search_by_group_each_page(driver, group, current_page):

    logger = getLogger()
    logger.info('method [search_by_group_each_page] start, group is {0}, current page is {1}'.format(group, current_page))
    group_url = config.load_value('search', 'search_by_group_url', '')
    url = group_url.format(group, current_page)
    end_page_flag = False
    artifact_list = []

    try:
        driver.get(url)
        end_page_flag = check_end_page(driver)
        elements_ims = driver.find_elements_by_class_name('im')
        if len(elements_ims):
            for element_ims in elements_ims:
                element_href = element_ims.find_element_by_tag_name('a')
                href_text = element_href.get_attribute('href')
                if href_text:
                    logger.info('href is {0}'.format(href_text))
                    artifact_list.append(href_text)

    except TimeoutException as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())

    except Exception as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())

    logger.info('method [search_by_group_each_page] end, group is {0}, current page is {1}'.format(group, current_page))
    return end_page_flag, artifact_list


# 查看是否为最后一页
def check_end_page(driver):

    logger = getLogger()
    logger.info('method [check_end_page] start')

    element_nav = driver.find_element_by_class_name('search-nav')
    elements_li = element_nav.find_elements_by_tag_name('li')
    li_len = len(elements_li)
    element_next = elements_li[li_len - 1]
    next_a = element_next.find_elements_by_tag_name('a')
    if next_a:
        end_page_flag = False
    else:
        end_page_flag = True

    logger.info("method [check_end_page] end, end page flag is {0}".format(end_page_flag))
    return end_page_flag


# 根据group查询artifact信息，返回url list
def search_by_group(driver, group):

    logger = getLogger()
    logger.info('method [search_by_group] start, group is {0}'.format(group))
    end_page_flag = False
    current_page = 1
    artifact_list = []

    while not end_page_flag:
        end_page_flag, result_list = search_by_group_each_page(driver, group, current_page)
        current_page += 1
        for result in result_list:
            if result in artifact_list:
                continue
            else:
                artifact_list.append(result)
        time.sleep(3)

    logger.info('method [search_by_group] end, group is {0}'.format(group))
    return artifact_list


# group id，artifact和url存入groupId_artifact表
def set_artifact(url_list):

    logger = getLogger()
    logger.info("method [set_artifact] start")

    for url in url_list:
        query = GroupIdArtifact.select().where(GroupIdArtifact.url == url)
        if len(query):
            continue
        else:
            # url: https://mvnrepository.com/artifact/org.springframework/spring-jdbc
            split_list = url.split('/')
            if len(split_list) == 6:
                groupId = split_list[-2]
                artifact = split_list[-1]
                if groupId and artifact:
                    GroupIdArtifact.create(
                        groupId=groupId,
                        artifact=artifact,
                        url=url,
                        proceed=False,
                    )
            else:
                continue
    logger.info("method [set_artifact] end")


# 取得version信息
def get_version(driver):
    logger = getLogger()
    logger.info("method [get_version] start")
    version_list = []

    query = GroupIdArtifact.select().where(GroupIdArtifact.proceed==False)
    for item in query:
        result_list = get_version_by_artifact(driver, item.url)
        set_version(result_list)
        item.proceed = True
        item.save()
        time.sleep(2)

    logger.info("method [get_version] end")


# 通过groupId_artifact表中存储的url，打开version列表页面，获取各version的url
def get_version_by_artifact(driver, url):
    logger = getLogger()
    logger.info("method [get_version_by_artifact] start, url is {0}".format(url))

    version_list = []

    try:
        driver.get(url)
        element_container = driver.find_elements_by_class_name('gridcontainer')
        if element_container:
            elements_version = element_container[0].find_elements_by_class_name('vbtn')
            for element in elements_version:
                version_list.append(element.get_attribute('href'))

    except TimeoutException as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
    except Exception as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())

    logger.info("method [get_version_by_artifact] end")
    return version_list


# group id，artifact，version和url存入groupId_artifact_version表
def set_version(version_list):
    logger = getLogger()
    logger.info("method [set_version] start")

    for url in version_list:
        query = GroupArtifactVersion.select().where(GroupArtifactVersion.url == url)
        if len(query):
            continue
        else:
            split_list = url.split('/')
            version = split_list[-1]
            artifact = split_list[-2]
            groupId = split_list[-3]
            GroupArtifactVersion.create(
                groupId=groupId,
                artifact=artifact,
                version=version,
                url=url,
                proceed=False
            )

    logger.info("method [set_version] end")


# 通过GroupArtifactVersion表中存储的url，打开version详细页面，获取其他group artifact的url并存入groupId_artifact表中
def get_artifact_by_version_page(driver):
    logger = getLogger()
    logger.info("method [get_artifact_by_version_page] start")

    query = GroupArtifactVersion.select().where(GroupArtifactVersion.searched==False)
    for item in query:
        result_list = []
        try:
            logger.info('url is {0}'.format(item.url))
            driver.get(item.url)
            elements_tables = driver.find_elements_by_class_name('version-section')
            for element in elements_tables:
                element_h = element.find_element_by_tag_name('h2')
                if element_h:
                    text = element_h.text
                    if text.startswith('Compile Dependencies') or text.startswith('Provided') or text.startswith(
                            'Test Dependencies'):
                        elements_tr = element.find_elements_by_xpath(".//tbody/tr")
                        for element_tr in elements_tr:
                            element_td = element_tr.find_elements_by_tag_name('td')[2]
                            element_a = element_td.find_elements_by_tag_name('a')
                            if len(element_a) == 2:
                                element_a = element_td.find_elements_by_tag_name('a')[1]
                                url = element_a.get_attribute('href')
                                result_list.append(url)
            logger.info('result_list length is {0}'.format(len(result_list)))
            set_artifact(result_list)
            item.searched = True
            item.save()

        except TimeoutException as e:
            logger.info(traceback.format_exc())
            print(traceback.format_exc())
        except Exception as e:
            logger.info(traceback.format_exc())
            print(traceback.format_exc())

    logger.info("method [get_artifact_by_version_page] end")


# 登录首页，输入关键词并查询
def search(driver, keyword):

    logger = getLogger()
    logger.info('method [search] start, keyword is {0}'.format(keyword))
    home_page_url = config.load_value('search', 'home_page_url', '')
    search_result = ''
    try:
        driver.get(home_page_url)

        element_search = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, 'query'))
        )
        key_word_input_wait = config.load_value('search', 'key_word_input_wait', '0')
        if key_word_input_wait:
            wait_milliseconds = int(key_word_input_wait)
            for letter in keyword:
                curr_wait_milliseconds = random.randint(1, wait_milliseconds)
                time.sleep(curr_wait_milliseconds / 1000)
                element_search.send_keys(letter)
        else:
            element_search.send_keys(keyword)

        element_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'button'))
        )
        key_word_button_click_wait = config.load_value('search', 'key_word_button_click_wait', '0')
        if key_word_button_click_wait:
            wait_milliseconds = int(key_word_button_click_wait)
            wait_milliseconds = random.randint(1, wait_milliseconds)
            time.sleep(wait_milliseconds / 1000)
        element_button.click()

        search_result = 'success'
    except TimeoutException as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'
    except Exception as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'

    logger.info("method [search] end")
    return search_result


# 取得最大页码
def get_page_count(driver):

    logger = getLogger()
    logger.info('method [get_page_count] start')

    elements_div = driver.find_element_by_id('maincontent')
    element_h = elements_div.find_element_by_tag_name('h2')
    result_text = element_h.text
    result_list = result_text.split(' ')
    result_count = result_list[1]
    print(result_count)
    page_count = min(math.ceil(int(result_count)/10), 5)
    print(page_count)
    logger.info('method [get_page_count] end, page count is {0}'.format(page_count))
    return page_count


# 取得group id，artifact和url，返回url列表
def get_artifacts(driver, page_count, keyword):

    logger = getLogger()
    logger.info('method [get_artifacts] start, keyword is {0}'.format_map(keyword))

    current_page = 1
    url_list = []
    while current_page <= page_count:
        return_url = get_artifact_by_page(driver, current_page, keyword)
        for url in return_url:
            if url in url_list:
                continue
            url_list.append(url)
        current_page += 1

        time.sleep(3)
    logger.info('method [get_page_count] end')
    return url_list


# 分页获取artifact信息
def get_artifact_by_page(driver, current_page, keyword):

    logger = getLogger()
    logger.info("method [get_artifact_by_page] start, current page is {0}".format(current_page))

    # 读取url
    url_format = config.load_value('search', 'search_artifact_by_page_url')
    url = url_format.format(keyword, current_page)
    artifact_list = []
    try:
        driver.get(url)
        elements_ims = driver.find_elements_by_class_name('im')
        if len(elements_ims):
            for element_ims in elements_ims:
                element_href = element_ims.find_element_by_tag_name('a')
                href_text = element_href.get_attribute('href')
                if href_text:
                    artifact_list.append(href_text)

    except TimeoutException as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'
    except Exception as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'

    logger.info("method [get_artifact_by_page] end, current page is {0}".format(current_page))
    return artifact_list


if __name__ == '__main__':

    url = "https://mvnrepository.com/artifact/org.springframework/spring-dao/2.0-m4"
    driver = webdriver.Chrome()
    driver.get(url)
    elements_tables = driver.find_elements_by_class_name('version-section')
    for element in elements_tables:
        element_h = element.find_element_by_tag_name('h2')
        if element_h:
            text = element_h.text
            if text.startswith('Compile Dependencies') or text.startswith('Provided') or text.startswith(
                    'Test Dependencies'):
                elements_tr = element.find_elements_by_xpath(".//tbody/tr")
                for element_tr in elements_tr:
                    element_td = element_tr.find_elements_by_tag_name('td')[2]
                    element_a = element_td.find_elements_by_tag_name('a')
                    if len(element_a) == 2:
                        element_a = element_td.find_elements_by_tag_name('a')[1]
                        url = element_a.get_attribute('href')








