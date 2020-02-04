# -*- coding:utf8 -*-
import math

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import datetime, random, time, traceback

from biz.orm import GroupIdArtifact
from utils.common import ConfigUtil
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


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


def search_by_group(driver, group):
    logger = getLogger()
    logger.info('method [search] start, group is {0}'.format(group))
    group_url = config.load_value('search', 'search_by_group_url', '')
    url = group_url.format(group, 11)
    print(url)
    try:
        driver.get(url)
        element_nav = driver.find_element_by_class_name('search-nav')
        elements_li = element_nav.find_elements_by_tag_name('li')
        li_len = len(elements_li)
        print(li_len)
        element_next = elements_li[li_len-1]
        next = element_next.find_elements_by_tag_name('a')
        if next:
            print('yeah')
        else:
            print('no')

    except TimeoutException as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'
    except Exception as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'

    logger.info("method [search] end")
    # return search_result


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


# group id，artifact和url存入数据库
def set_artifact(url_list):

    logger = getLogger()
    logger.info("method [set_artifact] start")

    for url in url_list:
        query = GroupIdArtifact.select().where(GroupIdArtifact.url == url)
        if len(query):
            continue
        else:
            # url:https://mvnrepository.com/artifact/org.springframework/spring-jdbc
            split_list = url.split('/')
            groupId = split_list[-2]
            artifact = split_list[-1]
            if groupId and artifact:
                GroupIdArtifact.create(
                    groupId=groupId,
                    artifact=artifact,
                    url=url,
                )
    logger.info("method [set_artifact] end")


# 取得version信息
def get_version():
    logger = getLogger()
    logger.info("method [get_orders] start")

    query = GroupIdArtifact.select()
    for item in query:
        version_list = get_version_by_artifact(item.url)
        set_version(version_list)


def get_version_by_artifact(driver, url):
    logger = getLogger()
    logger.info("method [get_orders] start")

    version_list = []

    try:
        driver.get(url)
        element_container = driver.find_element_by_class_name('gridcontainer')
        if len(element_container):
            elements_tbody = element_container.find_elements_by_tag_name('tbody')
            print(len(elements_tbody))

    except TimeoutException as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'
    except Exception as e:
        logger.info(traceback.format_exc())
        print(traceback.format_exc())
        search_result = 'failure'
    return version_list

def set_version():
    pass


def get_order_detail(driver, order_info):

    logger = getLogger()
    logger_custom = getLogger('custom')
    logger.info("method [get_order_detail] start")

    shop_region = config.load_value('review', 'shop_region', 'US')
    url_format = config.load_value(shop_region, 'request_review_url')
    url = url_format.format(order_info.order_id)
    str_timezones = config.load_value(shop_region, 'default_timezone')
    list_timezone = str_timezones.split(',')

    try:
        driver.get(url)
        # logger.info("get_order_detail, order id: {0}".format(order_info.order_id))
        logger.info("get_order_detail for order: {0}".format(order_info.order_id))
        time.sleep(3)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                (By.CSS_SELECTOR, 'span[data-test-id="order-summary-shipby-value"]')
            )),
            EC.presence_of_element_located((
                (By.CSS_SELECTOR, 'span[data-test-id="order-summary-purchase-date-value"]')
            ))
        )
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((
                (By.CSS_SELECTOR, 'div[data-test-id="shipping-section-buyer-address"]')
            )),
            EC.presence_of_element_located((
                (By.CSS_SELECTOR, '.order-details-bordered-box-notes-feedback')
            ))
        )
        # ship date, format: Thu, Dec 5, 2019  or  Thu, 5 Dec 2019
        elements_span = driver.find_elements_by_css_selector('span[data-test-id="order-summary-shipby-value"]')
        logger.info("ship_date elements_span length: {0}".format(len(elements_span)))
        if len(elements_span):
            element_span = elements_span[0]
            # logger.info("ship_date text: {0}".format(element_span.text.strip()))
            order_info.ship_date = element_span.text.strip()
            order_info.ship_date = datetime.datetime.strptime(order_info.ship_date, "%a, %b %d, %Y")
            # order_info.ship_date = DateUtil.convert_shipdate(order_info.ship_date)
            # logger.info("ship_date datetime: {0}".format(order_info.ship_date))

        # purchase date, format: Wed, Dec 4, 2019, 8:27 AM PST
        elements_span = driver.find_elements_by_css_selector('span[data-test-id="order-summary-purchase-date-value"]')
        logger.info("purchase_date elements_span length: {0}".format(len(elements_span)))
        if len(elements_span):
            element_span = elements_span[0]
            # logger.info("purchase_date text: {0}".format(element_span.text.strip()))
            order_info.purchase_date = DateUtil.strip_tz_str(element_span.text, list_timezone)
            order_info.purchase_date = datetime.datetime.strptime(order_info.purchase_date, "%a, %b %d, %Y, %I:%M %p")
            # logger.info("purchase_date datetime: {0}".format(order_info.purchase_date))

        # ship address
        elements_div = driver.find_elements_by_css_selector('div[data-test-id="shipping-section-buyer-address"]')
        logger.info("ship address elements_div length: {0}".format(len(elements_div)))
        if len(elements_div):
            element_div = elements_div[0]
            elements_span = element_div.find_elements_by_xpath('.//span')
            if shop_region == 'US':
                for i, element_span in enumerate(elements_span):
                    # logger.info("index: {0}, text: {1}".format(i, element_span.text))
                    if i == 0:
                        order_info.ship_address = element_span.text.split(',')[0].strip().upper()
                    # logger.info("order_info.ship_address: {0}".format(order_info.ship_address))
                    elif i == 2:
                        order_info.ship_region = element_span.text.strip().upper()
                    # logger.info("order_info.ship_region: {0}".format(order_info.ship_region))
                    elif i == 4:
                        order_info.ship_zip_code = element_span.text.strip()
            else:
                ship_state_index = len(elements_span) - 1
                ship_zip_code_index = len(elements_span) - 2
                for i, element_span in enumerate(elements_span):
                    # logger.info("index: {0}, text: {1}".format(i, element_span.text))
                    if i == 1:
                        order_info.ship_address = element_span.text.split(',')[0].strip().upper()
                    # logger.info("order_info.ship_address: {0}".format(order_info.ship_address))
                    elif i == 2:
                        order_info.ship_region = element_span.text.strip().upper()
                    # logger.info("order_info.ship_region: {0}".format(order_info.ship_region))
                    elif i == ship_zip_code_index:
                        order_info.ship_zip_code = element_span.text.strip()
                    # logger.info("order_info.ship_zip_code: {0}".format(order_info.ship_zip_code))
                    elif i == ship_state_index:
                        order_info.ship_state = element_span.text.strip().upper()
                    
        if order_info.ship_address and len(order_info.ship_address) and order_info.ship_region and len(order_info.ship_region):
            # 取得UTC并设置到buyer_time_zone
            if shop_region == 'US':
                order_info.buyer_time_zone = TimeZoneUtil.getTimeZone(order_info.ship_region, 'UTC-8')
                # logger.info("order_info.buyer_time_zone: {0}".format(order_info.buyer_time_zone))
            else:
                order_info.buyer_time_zone = TimeZoneUtil.getTimeZone(order_info.ship_state, 'UTC+1')
            

        # rating
        elements_feedback = driver.find_elements_by_css_selector('.order-details-bordered-box-notes-feedback')
        logger.info("elements_feedback length: {0}".format(len(elements_feedback)))
        for element_feedback in elements_feedback:
            elements_i = element_feedback.find_elements_by_tag_name("i")
            for element_i in elements_i:
                class_property = element_i.get_attribute('class')
                # logger.info("index: {0}, class_property: {1}".format(i, class_property))
                if 'a-star-1' in class_property:
                    order_info.buyer_rating = 1
                elif 'a-star-2' in class_property:
                    order_info.buyer_rating = 2
                elif 'a-star-3' in class_property:
                    order_info.buyer_rating = 3
                elif 'a-star-4' in class_property:
                    order_info.buyer_rating = 4
                elif 'a-star-5' in class_property:
                    order_info.buyer_rating = 5
            if order_info.buyer_rating:
                elements_span = element_feedback.find_elements_by_css_selector('span[class="auto-word-break"]')
                logger.info("elements_span length: {0}".format(len(elements_span)))
                for element_span in elements_span:
                    element_span_text = element_span.text.strip()
                    if element_span_text:
                        element_span_text = element_span.text[len('Comments : '):].strip('"')
                        order_info.buyer_comment = element_span_text
        order_info.refund = check_refund(driver)

    except Exception as e:
        logger.info(traceback.format_exc())

    logger.info("method [get_order_detail] end")

    return order_info


if __name__ == '__main__':

    driver = webdriver.Chrome()
    # url = "https://mvnrepository.com/artifact/org.springframework/spring-context"
    # get_version_by_artifact(driver, url)
    search_by_group(driver, 'org.springframework.boot')





