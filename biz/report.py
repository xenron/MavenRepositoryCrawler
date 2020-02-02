import datetime, logging, poplib, random, sys, time
import pandas as pd

from biz.orm import Job, RequestReviewHistory
from utils.log import getLogger


'''
Usage:

python biz/report.py order
'''

def export_order():

    logger = getLogger()
    logger.info('method [export_order] start')

    query = Job.select()
    df = pd.DataFrame(
        columns=(
            'order_id', 'buyer_name', 'purchase_date', 'ship_address', 'ship_region',
            'ship_date', 'ship_zip_code', 'buyer_rating', 'buyer_comment', 'refund',
            'processed_date', 'processed_status',
        )
    )

    if len(query):
        for i, record in enumerate(query):
            df.loc[i, 'order_id'] = record.order.order_id
            df.loc[i, 'buyer_name'] = record.order.buyer_name
            df.loc[i, 'purchase_date'] = record.order.purchase_date
            df.loc[i, 'ship_address'] = record.order.ship_address
            df.loc[i, 'ship_region'] = record.order.ship_region
            df.loc[i, 'ship_date'] = record.order.ship_date
            df.loc[i, 'ship_zip_code'] = record.order.ship_zip_code
            df.loc[i, 'buyer_rating'] = record.order.buyer_rating
            df.loc[i, 'buyer_comment'] = record.order.buyer_comment
            df.loc[i, 'refund'] = record.order.refund
            df.loc[i, 'processed_date'] = record.processed_date
            df.loc[i, 'processed_status'] = record.processed_status

        now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        path = "output/order_{0}.xls".format(now_time)
        df.to_excel(path)

    logger.info('method [export_order] end')


def export_history_all():

    logger = getLogger()
    logger.info('method [export_history_all] start')

    query = RequestReviewHistory.select()
    df = pd.DataFrame(
        columns=(
            'order_id', 'buyer_name', 'purchase_date', 'ship_address', 'ship_region',
            'ship_date', 'ship_zip_code', 'buyer_rating', 'buyer_comment', 'refund',
            'create_datetime', 'processed_status',
        )
    )

    if len(query):
        for i, record in enumerate(query):
            df.loc[i, 'order_id'] = record.order.order_id
            df.loc[i, 'buyer_name'] = record.order.buyer_name
            df.loc[i, 'purchase_date'] = record.order.purchase_date
            df.loc[i, 'ship_address'] = record.order.ship_address
            df.loc[i, 'ship_region'] = record.order.ship_region
            df.loc[i, 'ship_date'] = record.order.ship_date
            df.loc[i, 'ship_zip_code'] = record.order.ship_zip_code
            df.loc[i, 'buyer_rating'] = record.order.buyer_rating
            df.loc[i, 'buyer_comment'] = record.order.buyer_comment
            df.loc[i, 'refund'] = record.order.refund
            df.loc[i, 'create_datetime'] = record.create_datetime
            df.loc[i, 'processed_status'] = record.processed_status

        now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        path = "output/history_{0}.xls".format(now_time)
        df.to_excel(path)

    logger.info('method [export_history_all] end')


def test_main():
    pass


def test_main():
    main()


if __name__ == '__main__':

    if len(sys.argv) == 1:
        main()
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'order':
            export_order()
        elif sys.argv[1] == 'history_all':
            export_history_all()
    elif len(sys.argv) == 3 and sys.argv[1] == 'test' and sys.argv[2] == 'main':
        test_main()
    else:
        pass

