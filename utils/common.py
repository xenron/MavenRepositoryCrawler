import configparser, datetime, pytz, time
from selenium.webdriver.common.keys import Keys


def __singleton(cls):
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


class SeleniumUtil(object):

    @staticmethod
    def moveEnd(driver):
        driver.find_element_by_tag_name("body").send_keys(Keys.END)
        time.sleep(1)


class TimeZoneUtil(object):

    abbr_time_zone_list = None
    region_time_zone_list = None

    @staticmethod
    def getTimeZone(region, default_zone='UTC-8'):

        if not TimeZoneUtil.abbr_time_zone_list:
            # TimeZoneUtil.abbr_time_zone_list = { tz.abbreviation: tz.standard_time for tz in TimeZone.select() }
            TimeZoneUtil.abbr_time_zone_list = {tz.abbreviation: tz.utc for tz in Region.select().where(Region.usage == '1')}
        if not TimeZoneUtil.region_time_zone_list:
            # TimeZoneUtil.region_time_zone_list = { tz.state: tz.standard_time for tz in TimeZone.select() }
            TimeZoneUtil.region_time_zone_list = {tz.state: tz.utc for tz in Region.select().where(Region.usage == '1')}
        result = default_zone
        if region in TimeZoneUtil.abbr_time_zone_list:
            result = TimeZoneUtil.abbr_time_zone_list[region]
        elif region in TimeZoneUtil.region_time_zone_list:
            result = TimeZoneUtil.region_time_zone_list[region]

        return result


class ConfigUtil(object):

    def __init__(self, config_path='config.ini'):

        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')

    def load_value(self, key_base, key_sub, default_value=''):

        result = ""
        if key_base and key_sub:
            # check key_base not exist
            if not key_base in self.config.sections():
                pass
            # check key_sub exist
            elif not key_sub in dict(self.config.items(key_base)):
                pass
            # check key_base+key_sub is empty
            elif self.config.get(key_base, key_sub):
                result = self.config.get(key_base, key_sub)
        if len(result) == 0 and default_value and len(default_value):
            result = default_value
        return result

    def load_pair(self, key_base, key_sub, default_value=''):

        result = ""
        result = self.load_value(key_base, key_sub, default_value)
        if result and len(result.split(',')) > 1:
            result = result.split(',')

        return result

    # work_time=0830:1730
    # work_time=1:0830:1730|2:0730:2230|5:1110:2359
    def load_work_time(self, key_base, key_sub, default_value=''):

        result = ""
        result = self.load_value(key_base, key_sub, default_value)
        if result:
            # work_time={1:[0830,1730], 2:[0730,2230], 5:[1110:2359]}
            if '|' in result:
                work_time_dict = {}
                for day_info in result.split('|'):
                    time_info = day_info.split(':')
                    work_time_dict[time_info[0]] = [time_info[1], time_info[2]]
                result = work_time_dict
            # work_time=0830:1730
            else:
                result = result.split(':')

        return result


class TypeUtil(object):
    @staticmethod
    def str_to_bool(str):
        return True if str.lower() == 'true' else False

class DateUtil(object):

    @staticmethod
    def get_now():
        return datetime.datetime.now()

    @staticmethod
    def get_tomorrow_datetime(datetime_input):
        datetime_tomorrow = datetime_input + datetime.timedelta(days=1)
        return datetime_tomorrow

    @staticmethod
    def get_today_start_datetime(datetime_input):
        # print('input datetime: ', datetime_input)
        str_datetime_today = datetime_input.strftime("%Y-%m-%d")
        datetime_today_start = datetime.datetime.strptime(str_datetime_today, "%Y-%m-%d")
        return datetime_today_start

    @staticmethod
    def get_today_start_timestamp(datetime_input):
        # print('input datetime: ', datetime_input)
        datetime_today_start = DateUtil.get_today_start_datetime(datetime_input)
        # print('datetime_today_start: ', datetime_today_start)
        time_stamp = int(time.mktime(datetime_today_start.timetuple())) * 1000
        return time_stamp

    @staticmethod
    def get_today_end_timestamp(datetime_input):
        time_stamp = DateUtil.get_tomorrow_start_timestamp(datetime_input) - 1000
        return time_stamp

    @staticmethod
    def get_tomorrow_start_timestamp(datetime_input):
        # print('input datetime: ', datetime_input)
        datetime_tomorrow = DateUtil.get_tomorrow_datetime(datetime_input)
        str_tomorrow = datetime_tomorrow.strftime("%Y-%m-%d")
        datetime_tomorrow_start = datetime.datetime.strptime(str_tomorrow, "%Y-%m-%d")
        # print('datetime_tomorrow_start: ', datetime_tomorrow_start)
        time_stamp = int(time.mktime(datetime_tomorrow_start.timetuple())) * 1000
        return time_stamp

    @staticmethod
    def get_now_for_tz(tz=None):
        now = None
        if tz:
            now = datetime.datetime.now().astimezone(pytz.timezone(tz))
            now_format = now.strftime("%Y-%m-%d %H:%M:%S")
            local_time = datetime.datetime.strptime(now_format, "%Y-%m-%d %H:%M:%S")
            return local_time
        else:
            # cst_tz = timezone('Asia/Shanghai')
            # now = datetime.datetime.now().replace(tzinfo=cst_tz)
            now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Shanghai'))
            now_format = now.strftime("%Y-%m-%d %H:%M:%S")
            local_time = datetime.datetime.strptime(now_format, "%Y-%m-%d %H:%M:%S")
            return local_time
            
        return now

    @staticmethod
    def strip_tz_str(str_datetime, list_timezone):
        # index_pst = str_datetime.find('PST')
        # index_pdt = str_datetime.find('PDT')
        # index_pst = str_datetime.find('MET')
        # index_pdt = str_datetime.find('MEST')
        # index = max(index_pdt, index_pst)
        index = 0
        for timezone in list_timezone:
            index = str_datetime.find(timezone)
            if index > 0:
                break
        return str_datetime[:index].strip()

    @staticmethod
    def get_now_for_pts(default_tz):
        # cst_tz = timezone('Asia/Shanghai')
        # now = datetime.datetime.now().replace(tzinfo=cst_tz)
        tz_full = DateUtil.get_tz_full_info(default_tz)
        now = datetime.datetime.now().astimezone(pytz.timezone(tz_full))
        return now

    @staticmethod
    def get_tz_full_info(tz_utc):
        tz_full = None
        tz_full_orm = TimeZone.select(TimeZone.city).where(TimeZone.utc == tz_utc).limit(1)
        tz_full = tz_full_orm[0].city
        # if tz_abbr == "US":
        #     tz_full = 'America/Los_Angeles'
        # elif tz_abbr == 'MST':
        #     tz_full = 'America/Edmonton'
        # elif tz_abbr == 'CST':
        #     tz_full = 'America/Mexico_City'
        # elif tz_abbr == 'EST':
        #     tz_full = 'America/New_York'
        # elif tz_abbr == 'BJS':
        #     tz_full = 'Asia/Shanghai'
        # if tz_abbr == 'UTC-8':
        #     tz_full = 'America/Los_Angeles'
        # elif tz_abbr == 'UTC-7':
        #     tz_full = 'America/Edmonton'
        # elif tz_abbr == 'UTC-6':
        #     tz_full = 'America/Mexico_City'
        # elif tz_abbr == 'UTC-5':
        #     tz_full = 'America/New_York'
        # elif tz_abbr == 'UTC+8':
        #     tz_full = 'Asia/Shanghai'
        # elif tz_abbr == 'UTC+0':
        #     tz_full = 'Europe/Dublin'
        # elif tz_abbr == 'UTC+1':
        #     tz_full = 'Europe/Berlin'
        # elif tz_abbr == 'UTC+2':
        #     tz_full = 'Europe/Helsinki'
        # elif tz_abbr == 'UTC+3':
        #     tz_full = 'Europe/Moscow'

        return tz_full

    @staticmethod
    def convert_datetime(datetime_input, to_tz_utc):
        # from_tz = get_tz_full_info(from_tz_abbr)
        to_tz = DateUtil.get_tz_full_info(to_tz_utc)
        result = datetime_input.astimezone(pytz.timezone(to_tz))
        return result

    # @staticmethod
    # def convert_shipdate(datetime_input):
    #     sub_ship_date = datetime_input[-6:]
    #     # format is 'Thu, Dec 5, 2019'
    #     if sub_ship_date.startswith(','):
    #         ship_date = datetime.datetime.strptime(datetime_input, "%a, %b %d, %Y")
    #     # format is 'Thu, 5 Dec 2019'
    #     else:
    #         ship_date = datetime.datetime.strptime(datetime_input, "%a, %d %b %Y")
    #     return ship_date


class ClassUtil(object):

    @staticmethod
    def object_to_dict(objet):

        properties = {}

        for name in dir(objet):
            value = getattr(objet, name)

            if name.startswith('__') or name.startswith('_') or callable(value):
                continue

            properties[name] = value

        return properties


    @staticmethod
    def get_instance_by_dict(object, properties):

        for name, value in dir(object):
            value = getattr(object, name)

            if name.startswith('__') or name.startswith('_') or callable(value):
                continue

            properties[name] = value

        return properties


if __name__ == '__main__':

    # print('00000000000')
    # result = get_now()
    # print(result)
    # print('11111111111')
    # result = get_tomorrow_datetime()
    # print(result)
    # print('22222222222')
    # result = get_tomorrow_start_second()
    # print(result)
    # print('33333333333')
    # print('11/30/2019 3:52 PM PST')
    # result = datetime.datetime.strptime('11/30/2019 3:52 PM', "%m/%d/%Y %I:%M %p")
    # print(result)
    # print('44444444444')
    # index = '11/30/2019 3:52 PM PST'.find(' PST')
    # print('11/30/2019 3:52 PM PST'[:index])
    # print(get_now_for_tz('America/New_York'))
    # print(DateUtil.get_now_for_tz('Europe/Moscow'))
    # print(pytz.country_timezones('ie'))
    # result = datetime.datetime.strptime('04,01,2019 15:08', "%m,%d,%Y %H:%M")
    # print(result)
    # dateformat1 = '11/30/2019 3:52 PM'
    # if (dateformat1.find('AM') > 0) or (dateformat1.find('PM') > 0) :
    #     print("yes")
    # str_date = 'Thu, 5 Dec 2019'
    # str_date = 'Thu, Dec 5, 2019'
    # sub_date = str_date[-6:]
    # if sub_date.startswith(','):
    #     ship_date = datetime.datetime.strptime(str_date, "%a, %b %d, %Y")
    #
    # else:
    #     ship_date = datetime.datetime.strptime(str_date, "%a, %d %b %Y")
    # print(ship_date)
    # date = datetime.datetime.strptime(str_date, "%d/%m/%Y %H:%M")
    date = datetime.datetime.now().astimezone(pytz.timezone('EUROPE/BERLIN'))
    print(date)

    # pass
