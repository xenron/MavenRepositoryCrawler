# -*- coding:utf8 -*-
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import datetime, random, time, traceback
from utils.common import ConfigUtil, DateUtil, SeleniumUtil, TimeZoneUtil
from utils.log import getLogger


# 读取配置文件
config = ConfigUtil()


# 登录Amazon，返回结果为success、otp或failure
def login(driver, keyword):

    logger = getLogger()
    logger.info("method [login] start, keyword is {0}".format(keyword))
    home_page_url = config.load_value('search', 'home_page_url', '')
    
    try:
        driver.get(home_page_url)

        time.sleep(3)

        # input keyword
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

    except TimeoutException as e:
        logger.info(traceback.format_exc())

    logger.info("method [login] end")


# 获取orders列表每页上的order信息
def get_order_by_page(driver, page_no, timestamp_range_start, timestamp_range_end, record_count):

    logger = getLogger()
    logger.info("method [get_order_by_page] start")
    # 读取orders列表的url
    shop_region = config.load_value('review', 'shop_region', 'US')
    url_format = config.load_value(shop_region, 'orderlist_url')
    url_initial = url_format.format(page_no, timestamp_range_start, timestamp_range_end)

    orders = []
    # 读取Amazon页面可能显示的时区信息
    str_timezones = config.load_value(shop_region, 'default_timezone')
    list_timezone = str_timezones.split(',')

    try:
        driver.get(url_initial)
        logger.info("get_order_by_page, access url_initial: {0}".format(url_initial))
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'orders-table'))
        )
        time.sleep(5)
        elements_orders_table = driver.find_elements_by_id('orders-table')
        # logger.info("len(elements_orders_table): {0}".format(len(elements_orders_table)))
        if len(elements_orders_table):
            element_orders_table = elements_orders_table[0]
            elements_tr = None
            while True:
                elements_tr = element_orders_table.find_elements_by_tag_name('tr')
                # logger.info("len(elements_tr): {0}".format(len(elements_tr)))
                if len(elements_tr) > record_count:
                    break
                SeleniumUtil.moveEnd(driver)

            for element_tr in elements_tr:
                order_info = OrderInfo()
                elements_td = element_tr.find_elements_by_tag_name('td')
                # logger.info("len(elements_td): {0}".format(len(elements_td)))
                if len(elements_td):
                    for i, element_td in enumerate(elements_td):
                        # order date
                        if i == 1:
                            elements_div = element_td.find_elements_by_xpath('.//div/div/div')
                            
                            for j, element_div in enumerate(elements_div):
                                if j == 1:
                                    order_info.order_date = element_div.text
                                elif j == 2:
                                    order_info.order_date = order_info.order_date + " " + element_div.text
                            # 11/30/2019 3:52 PM PST
                            # logger.info("order_date text: {0}".format(order_info.order_date))
                            try:
                                order_info.order_date = DateUtil.strip_tz_str(order_info.order_date, list_timezone)
                                order_info.order_date = datetime.datetime.strptime(order_info.order_date,"%m/%d/%Y %I:%M %p")
                                # index_of_GM = order_info.order_date.find('GM')
                                # if index_of_GM < 0:
                                #     order_info.order_date = datetime.datetime.strptime(order_info.order_date, "%m/%d/%Y %I:%M %p")
                                # else:
                                #     str_date = order_info.order_date[:index_of_GM].strip()
                                #     order_info.order_date = datetime.datetime.strptime(str_date, "%d/%m/%Y %H:%M")
                            except Exception as e:
                                logger.info(traceback.format_exc())
                                continue
                            # logger.info("order_date datetime: {0}".format(order_info.order_date))
                        # order id & buyer name
                        elif i == 2:
                            elements_a = element_td.find_elements_by_tag_name('a')
                            for j, element_a in enumerate(elements_a):
                                if j == 0:
                                    order_info.order_id = element_a.text
                                elif j == 1:
                                    order_info.buyer_name = element_a.text
                        # customer option
                        elif i == 5:
                            elements_span = element_td.find_elements_by_xpath('.//div/div/div/span')
                            if len(elements_span):
                                element_span = elements_span[0]
                                order_info.customer_option = element_span.text

                if order_info.order_id:
                    # 判断order id是否在黑名单中
                    query = BlackOrderId.select().where(BlackOrderId.order_id == order_info.order_id)
                    if len(query) == 0:
                        orders.append(order_info)
                    else:
                        logger.info('order {0} already exists in black list'.format(order_info.order_id))
                        continue

    except Exception as e:
        logger.info(traceback.format_exc())
        raise e

    logger.info("method [get_order_by_page] end")

    return orders

# 取得全部订单信息
def get_orders(driver, keyword):

    logger = getLogger()
    logger_custom = getLogger('custom')

    logger.info("method [get_orders] start")

    orders = []
    current_page = 1
    max_page = 10
    order_count = 0


    # 获取查询订单的url
    shop_region = config.load_value('review', 'search_by_keyword_url', 'US')
    url_format = config.load_value(shop_region, 'orderlist_url')
    url_initial = url_format.format(current_page, timestamp_range_start, timestamp_range_end)
    logger.info("get_orders, access url_initial: {0}".format(url_initial))
    try:
        driver.get(url_initial)
        time.sleep(5)

        element_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'myo-layout'))
        )
        time.sleep(10)
        # 获取订单总数
        elements_summary = driver.find_elements_by_css_selector('.total-orders-heading')
        # logger.info("len(elements_summary): {0}".format(len(elements_summary)))
        if len(elements_summary):
            element_summary = elements_summary[0]
            elements_span = element_summary.find_elements_by_tag_name('span')
            # logger.info("len(elements_span): {0}".format(len(elements_span)))
            for element_span in elements_span:
                if element_span.text.endswith('orders'):
                    # order最多10000条
                    if '10000+ orders' in element_span.text:
                        order_count = 10000
                        logger_custom.info("search result is greater than 10000, but get first 10000, all order count: {0}".format(order_count))
                    else:
                        index = element_span.text.find(' orders')
                        order_count = int(element_span.text[:index])
        logger_custom.info("all order count: {0}".format(order_count))
        if order_count > 1:
            # 计算最大page数
            if (order_count % 50) > 0:
                max_page = (order_count // 50) + 1
            else:
                max_page = order_count // 50
            logger_custom.info("max_page: {0}".format(max_page))

            # 循环全部页数
            for i in range(1, max_page + 1):
                record_count = 50 if i < max_page else order_count - 50 * (i - 1)
                # 读取每页上的order
                orders_page = get_order_by_page(driver, i, timestamp_range_start, timestamp_range_end, record_count)
                orders = orders + orders_page
                logger_custom.info("get order info for page {0}, order(page) count: {1}, order(all) count: {2}".format(i, len(orders_page), len(orders)))
                time.sleep(10)

                # 读取配置文件中，等待 x ms后，点击登录
                early_stop = int(config.load_value('test', 'early_stop_order_list', '0'))
                if early_stop and i > early_stop:
                    break

    except Exception as e:
        logger.info(traceback.format_exc())
        raise e

    logger.info("method [get_orders] end")

    return orders


def request_review(driver, order_id):

    logger = getLogger()
    logger.info("method [request_review] start, order_id: {0}".format(order_id))
    shop_region = config.load_value('review', 'shop_region', 'EU')
    url_format = config.load_value(shop_region, 'request_review_url')
    result = ''
    # url = "https://sellercentral.amazon.com/orders-v3/order/{0}".format(order_id)
    url = url_format.format(order_id)
    driver.get(url)
    time.sleep(3)
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '//span[@data-test-id="request-a-review-button"]'))
    )
    elements_span = driver.find_elements_by_css_selector('span[data-test-id="request-a-review-button"]')
    logger.info("len(elements_span): {0}".format(len(elements_span)))
    if len(elements_span):
        element_span = elements_span[0]
        # [Request a Review] button
        elements_a = element_span.find_elements_by_xpath(".//span/a")
        logger.info("len(elements_a): {0}".format(len(elements_a)))
        if len(elements_a):
            element_a = elements_a[0]
            element_a.click()
            request_review_interval = int(config.load_value('request', 'request_review_interval', '5'))
            if not request_review_interval:
                request_review_interval = 5
            time.sleep(request_review_interval)

    # Request a Review
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '//h1[text()="Request a Review"]'))
    )
    elements_h1 = driver.find_elements_by_xpath("//h1[text()='Request a Review']")
    logger.info("len(elements_h1): {0}".format(len(elements_h1)))
    if len(elements_h1):
        elements_span = driver.find_elements_by_xpath("//span[text()='Not eligible at this time']")
        logger.info("len(elements_span): {0}".format(len(elements_span)))
        if len(elements_span):
            elements_div = driver.find_elements_by_xpath("//div[text()='You have already requested a review for this order.']")
            if len(elements_div):
                result = 'repeated'
            elements_div = driver.find_elements_by_xpath("//div[text()='You can’t use this feature to request a review outside the 4-30 day range after the order delivery date.']")
            if len(elements_div):
                result = 'not-eligible'
        else:
            elements_div = driver.find_elements_by_css_selector('div[class="ayb-reviews-button-container"]')
            logger.info("len(elements_div): {0}".format(len(elements_div)))
            if len(elements_div):
                element_div = elements_div[0]
                elements_button = element_div.find_elements_by_tag_name("button")
                # logger.info("len(elements_button): {0}".format(len(elements_button)))
                for element_button in elements_button:
                    if element_button.text == 'Yes':
                        logger.info('find yes button')
                        element_button.click()
                        request_review_interval = int(config.load_value('request', 'request_review_interval', '5'))
                        if not request_review_interval:
                            request_review_interval = 5
                        time.sleep(request_review_interval)
                        break
                elements_span = driver.find_elements_by_xpath("//span[text()='A review will be requested for this order.']")
                if len(elements_span):
                    result = 'completed'

    logger.info("method [request_review] end")
    return result


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


# def test_login(driver, name, email, password):

#     login_result = login(driver, name, email, password)
#     print(login_result)


# def test_click(driver):

#     url = 'https://www.amazon.com/gp/product/B07D4JXNV1'
#     click(driver, url)


# def test_search(driver):

#     key_word = 'pure water'
#     search_key_word = '+'.join(key_word.split(' '))
#     search(driver, search_key_word, [])


if __name__ == '__main__':

    driver = webdriver.Chrome()

    try:
        # test_search(driver)
        test_click(driver)
    finally:
        driver.quit()





