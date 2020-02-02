# -*- coding:utf8 -*-
from peewee import fn
from playhouse.shortcuts import model_to_dict, dict_to_model
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import datetime, peewee, random, sys, time, tqdm, traceback

from biz.amazon import login, check_home_page, get_orders, check_refund, check_feedback, request_review, get_order_detail
from biz.common import User
from biz.orm import Job, RequestReviewHistory, Order, OrderHistory
from biz.orm import initial_database, initial_table_blackorderid
from biz.reload import load_region_utc, load_black_order_id, load_time_zone
from utils.common import ClassUtil, ConfigUtil, DateUtil, TypeUtil
from utils.log import getLogger

'''
Usage:

python main.py
'''


# 读取配置文件
config = ConfigUtil()


# 登录Amazon，并把登录结果输出到log
def login_amazon(driver, user):

    logger = getLogger()
    logger.info('method [login_amazon] start')

    login_result = ''

    # 登录Amazon
    logger.info("user [{0}] try to login amazon.".format(user.email))
    login_result = login(driver, user.email, user.password)
    if login_result == 'failure':
        logger.info("user [{0}] login amazon failure.".format(user.email))
    elif login_result == 'success':
        logger.info("user [{0}] login amazon success.".format(user.email))
    elif login_result == 'otp':
        logger.info("user [{0}] login amazon success, but need input otp.".format(user.email))

    logger.info('method [login_amazon] end')

    return login_result


def create_order_record(order_info):
    order = Order.create(
        order_id=order_info.order_id,
        ship_date=order_info.ship_date,
        ship_address=order_info.ship_address,
        ship_state=order_info.ship_state,
        ship_region=order_info.ship_region,
        ship_zip_code=order_info.ship_zip_code,
        purchase_date=order_info.purchase_date,
        standard_time_zone=order_info.standard_time_zone,
        buyer_name=order_info.buyer_name,
        buyer_time_zone=order_info.buyer_time_zone,
        buyer_rating=order_info.buyer_rating,
        buyer_comment=order_info.buyer_comment,
        buyer_feedback=order_info.buyer_feedback
    )
    order_history = OrderHistory.create(
        order_id=order_info.order_id,
        ship_date=order_info.ship_date,
        ship_address=order_info.ship_address,
        ship_state=order_info.ship_state,
        ship_region=order_info.ship_region,
        ship_zip_code=order_info.ship_zip_code,
        purchase_date=order_info.purchase_date,
        standard_time_zone=order_info.standard_time_zone,
        buyer_name=order_info.buyer_name,
        buyer_time_zone=order_info.buyer_time_zone,
        buyer_rating=order_info.buyer_rating,
        buyer_comment=order_info.buyer_comment,
        buyer_feedback=order_info.buyer_feedback
    )
    return order


# 把符合条件的order插入到job表
def process_order():

    logger = getLogger()
    logger.info('method [process_order] start')

    # Job.truncate_table()
    shop_region = config.load_value('review', 'shop_region', 'US')

    day_after_shipped = int(config.load_value('order', 'day_after_shipped', '4'))

    # process all orders
    query = Order.select().where(
        (Order.refund == False) & (Order.buyer_feedback == True) & (Order.requested_review == False)
    )
    # logger.info("query result: {0}.".format(len(query)))

    if len(query) == 0:
        logger.info("no order need process")
        return

    for order in query:

        if order.ship_date == None:
            continue
        if order.ship_date < DateUtil.get_today_start_datetime(order.purchase_date):
            continue
        # logger.info("record info, id: {0}, ship_date: {1}".format(order.order_id, order.ship_date))
        now = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
        # logger.info("now pts: {0}".format(DateUtil.get_now_for_pts()))
        # logger.info("now no tz: {0}".format(DateUtil.get_now_for_pts().replace(tzinfo=None)))
        received_date = order.ship_date + datetime.timedelta(days=day_after_shipped)
        # ship_date = ship_date.replace(tzinfo=None)
        # logger.info("ship_date pts: {0}".format(ship_date))
        # logger.info("ship_date no tz: {0}".format(ship_date.replace(tzinfo=None)))
        # logger.info("datetime compare, now: {0}, ship_date: {1}".format(now, ship_date))
        if now > received_date:
            query = Job.select().where(Job.order==order.id)
            if len(query):
                pass
            else:
                Job.create(
                    order=order.id,
                    create_datetime=DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None),
                    update_datetime=DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None),
                    processed_status='pending',
                )

    logger.info('method [process_order] end')


def process_job(driver, request_review_start, request_review_end):

    logger = getLogger()
    logger.info('method [process_job] start')
    skip_request_review_action = config.load_value('review', 'skip_request_review_action', 'True')
    check_login_interval_default = int(config.load_value('review', 'check_login_interval', '100'))
    request_review_job_interval = int(config.load_value('review', 'request_review_job_interval', '30'))
    check_login_interval = 0
    request_review_by_customer_tz = config.load_value('review', 'request_review_by_customer_tz', 'False')
    shop_region = config.load_value('review', 'shop_region', 'EU')

    # process job
    query = Job.select().where(
        (Job.processed_status == 'pending') & \
        ((Job.process_datetime == None) | (Job.process_datetime < DateUtil.get_today_start_datetime(DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None))))
    ).order_by(Job.process_datetime.asc())
    logger.info("all job count: {0}".format(len(query)))

    # process request review
    if len(query):
        for i, job in enumerate(tqdm.tqdm(query)):

            if check_login_interval == check_login_interval_default:
                user_name = config.load_value('user', 'email')
                user_password = config.load_value('user', 'password')
                user = User(user_name, user_password)
                login_result = login_amazon(driver, user)
                check_login_interval = 0
            else:
                check_login_interval += 1

            # index = random.randint(0, len(query) - 1)
            # logger.info("index: {0}".format(index))
            # job = query[index]
            if request_review_by_customer_tz == 'True':
                tz_full_info = DateUtil.get_tz_full_info(job.order.buyer_time_zone)
            else:
                tz_full_info = DateUtil.get_tz_full_info(shop_region)
            # 索评时间，根据request_review_by_customer_tz而取值不同
            tz_time = DateUtil.get_now_for_tz(tz=tz_full_info).strftime('%H%M')
            # tz_full_info = DateUtil.get_tz_full_info(job.order.buyer_time_zone)
            # tz_time = DateUtil.get_now_for_tz(tz=tz_full_info).strftime('%H%M')
            logger.info("pts time: {0}, tz_time: {1}".format(DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None), DateUtil.get_now_for_tz(tz=tz_full_info)))
            logger.info("request_review_start: {0}, tz_time: {1}, request_review_end :{2}".format(request_review_start, tz_time, request_review_end))
            if request_review_start <= tz_time and tz_time <= request_review_end:
                logger.info("skip_request_review_action: {0}".format(skip_request_review_action))
                if skip_request_review_action == 'True':
                    request_result = 'test'
                else:
                    try:
                        request_result = request_review(driver, job.order.order_id)
                    except Exception as e:
                        request_result = 'exception'
                        logger.error(traceback.format_exc())
                logger.info("request_result: {0}".format(request_result))
                RequestReviewHistory.create(
                    order=job.order.id,
                    create_datetime=DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None),
                    update_datetime=DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None),
                    processed_status=request_result,
                )

                if request_result == 'not-eligible':
                    query = RequestReviewHistory.select().where(
                        (RequestReviewHistory.order == job.order.id) & (RequestReviewHistory.processed_status == 'not-eligible')
                    )
                    max_retry_times = int(config.load_value('review', 'max_retry_times', '0'))
                    if len(query) >= max_retry_times:
                        job.order.update_datetime = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                        job.order.request_review_datetime = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                        job.order.requested_review = True
                        job.order.save()
                        # job.process_datetime = None
                        job.processed_date = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                        job.processed_status = 'expired'
                    job.process_datetime = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None) + datetime.timedelta(days=2)
                    job.save()
                elif request_result in ['completed', 'repeated']:
                    job.order.update_datetime = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                    job.order.request_review_datetime = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                    job.order.requested_review = True
                    job.order.save()
                    job.processed_date = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                    job.processed_status = request_result
                    job.save()
                elif request_result == 'test':
                    job.order.update_datetime = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                    job.order.request_review_datetime = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                    job.order.requested_review = True
                    job.order.save()
                    job.processed_date = DateUtil.get_now_for_pts(shop_region).replace(tzinfo=None)
                    job.processed_status='test'
                    job.save()
            else:
                logger.info('wait for process next job.')
                time.sleep(request_review_job_interval)

    logger.info('method [process_job] end')


def get_order_info():

    logger = getLogger()
    logger_custom = getLogger('custom')

    logger.info('method [get_order_info] start')

    user_name = config.load_value('user', 'email')
    user_password = config.load_value('user', 'password')
    user = User(user_name, user_password)
    shop_region = config.load_value('review', 'shop_region')
    # request_review_time = config.load_work_time('review', 'request_review_time', '0830:1730')
    # request_review_start = request_review_time[0]
    # request_review_end = request_review_time[1]

    driver = webdriver.Chrome()        
    driver.implicitly_wait(2)

    try:
        logger_custom.info('login amazon')
        login_result = login_amazon(driver, user)
        max_retry_times = int(config.load_value('user', 'max_retry_times', '10'))
        # print("max_retry_times", max_retry_times)
        current_retry_times = 0

        if login_result == 'failure':
            logger_custom.info("login result: {0}".format(login_result))
            time.sleep(10)

        if login_result == 'otp':
            while current_retry_times < max_retry_times:
                current_retry_times += 1
                if check_home_page(driver):
                    login_result = 'success'
                    break
                else:
                    if current_retry_times == 1:
                        logger_custom.info('Please input one time password.')
                    logger_custom.info("wait for otp, sleep {0} seconds.".format(10*current_retry_times))
                    time.sleep(10*current_retry_times)

        logger.info("start get order info with detail")
        if login_result == 'success':
            time.sleep(5)
            driver.maximize_window()
            # change filter first to www.amazon.es
            if shop_region == 'EU':
                selector = Select(driver.find_element_by_id('sc-mkt-picker-switcher-select'))
                selector.select_by_visible_text("www.amazon.es")
                time.sleep(3)
            # change language to English
            selector = Select(driver.find_element_by_id('sc-lang-switcher-header-select'))
            selector.select_by_visible_text("English")
            time.sleep(3)
            # search order info
            order_list = get_orders(driver)
            # 循环每个订单，插入数据库
            logger.info('start insert orders into DB')
            for i, order_info in enumerate(tqdm.tqdm(order_list)):
                query = Order.select().where(Order.order_id == order_info.order_id)
                order = None
                if len(query):
                    # TODO 订单状态存在变更的可能性
                    continue

                order_info = get_order_detail(driver, order_info)
                if order_info.ship_date == None:
                    logger.info('order {0} ship_date is none, skip'.format(order_info.order_id))
                    continue
                if order_info.purchase_date == None:
                    logger.info('order {0} purchase_date is none, skip'.format(order_info.order_id))
                    continue
                order = create_order_record(order_info)

                # 读取配置文件中，等待 x ms后，点击登录
                early_stop = int(config.load_value('test', 'early_stop_order_detail', '0'))
                if early_stop and i > early_stop:
                    break

                if check_refund(driver):
                    order.refund = True
                else:
                    order.refund = False

                if check_feedback(driver, order):
                    order.buyer_feedback = True
                else:
                    order.buyer_feedback = False
                order.save()
        else:
            return

    except Exception as e:
        logger.error(traceback.format_exc())
    finally:
        driver.quit()

    logger.info('method [get_order_info] end')


def request_user_review():

    logger = getLogger()
    logger_custom = getLogger('custom')

    logger.info('method [request_user_review] start')

    user_name = config.load_value('user', 'email')
    user_password = config.load_value('user', 'password')
    user = User(user_name, user_password)
    request_review_time = config.load_work_time('review', 'request_review_time', '0830:1730')
    request_review_start = request_review_time[0]
    request_review_end = request_review_time[1]

    driver = webdriver.Chrome()        
    driver.implicitly_wait(2)

    try:
        login_result = login_amazon(driver, user)
        max_retry_times = int(config.load_value('user', 'max_retry_times', '10'))
        current_retry_times = 0

        if login_result == 'failure':
            time.sleep(10)

        if login_result == 'otp':
            while current_retry_times < max_retry_times:
                current_retry_times += 1
                if check_home_page(driver):
                    login_result = 'success'
                    break
                else:
                    # logger.info("sleep {0} seconds.".format(10*current_retry_times))
                    if current_retry_times == 1:
                        logger_custom.info('Please input one time password.')
                    logger_custom.info("wait for otp, sleep {0} seconds.".format(10*current_retry_times))
                        # logger.info("==============================")
                    time.sleep(10*current_retry_times)

        logger.info("start get order info with detail")
        if login_result == 'success':
            time.sleep(5)
            # change language to English
            selector = Select(driver.find_element_by_id('sc-lang-switcher-footer-select'))
            selector.select_by_visible_text("English")
            time.sleep(10)

            process_order()
            # process_job(request_review_start, request_review_end)
            time.sleep(6)
            process_job(driver, request_review_start, request_review_end)
        else:
            return

    except Exception as e:
        logger.error(traceback.format_exc())
    finally:
        driver.quit()

    logger.info('method [request_user_review] end')


if __name__ == '__main__':

    if config.load_value('system', 'init_database', 'False') == 'True':
        initial_database()
        # 加载各地区对应的utc到数据库
        load_region_utc('data/Region.xlsx')
        # 加载各utc对应的代表城市到数据库
        load_time_zone('data/TimeZone.xlsx')

    # if config.get('system', 'init_test_data') == 'True':
    #     initial_test_data()

    # 加载已索评过的order id
    initial_table_blackorderid()
    load_black_order_id('data/BlackOrderId.xlsx')

    if len(sys.argv) == 1:
        main()
        # import time,datetime
        # timeDateStr="2019-12-01 00:00:00"
        # time1=datetime.datetime.strptime(timeDateStr,"%Y-%m-%d %H:%M:%S")
        # secondsFrom1970=time.mktime(time1.timetuple())
        # print(secondsFrom1970)
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'get_order_info':
            get_order_info()
        elif sys.argv[1] == 'request_user_review':
            request_user_review()
    elif len(sys.argv) == 3 and sys.argv[1] == 'test':
        if sys.argv[2] == 'main':
            main()
        elif sys.argv[2] == 'process_order':
            test_process_order()
        elif sys.argv[2] == 'process_job':
            test_process_job()
        elif sys.argv[2] == 'switch_proxy':
            test_switch_proxy()
        elif sys.argv[2] == 'search_click':
            test_search_click()
        elif sys.argv[2] == 'log':
            test_log()
    elif len(sys.argv) == 3 and sys.argv[1] == 'show':
        if sys.argv[2] == 'order':
            for order in Order.select():
                print(order.order_id, order.buyer_rating)
    else:
        pass

