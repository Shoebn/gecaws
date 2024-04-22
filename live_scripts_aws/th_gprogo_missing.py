import logging
from gec_common import log_config
import web_db_connection
from datetime import date, datetime, timedelta
import sys

connection = web_db_connection.get_conn()
cursor = connection.cursor()

publishdate = sys.argv[1] #18122023
publish_date = datetime.strptime(str(publishdate),'%d%m%Y').strftime('%d %b %Y')
script_name = sys.argv[2] #th_gprogo

query_missing_result = "select notice_no,notice_type,method_name from cross_check_output where notice_no not in (select notice_no from tender where date(update_date) >= '"+ publish_date + "' and script_name ilike '" + script_name +"%')  and date(publish_date) >= '"+ publish_date + "' and script_name ilike '" + script_name +"%'"
cursor.execute(query_missing_result)
missing_result = cursor.fetchall()

logging.info(missing_result)
print(missing_result)
