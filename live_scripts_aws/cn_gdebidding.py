from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_gdebidding"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_gdebidding"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global page_no
    notice_data = tender()
    
    notice_data.script_name = 'cn_gdebidding'
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -take all the tabs data by cliking on below method ("Bidding Information Announcement  招标信息公告" and "Tender information notice  招标信息预告"notice_type=4),  ("Announcement of bidding results 招标结果公示" and "Announcement of Bidding Results  招标结果公告" notice_type=7),
    # ("Clarification and Correction Announcement  澄清更正公告"  notice_type=16),
    # "(Prequalification Announcement  资格预审公告)"

    if 'zbxxgg' in url or 'zbyg' in url:
        notice_data.notice_type = 4
    elif 'zbjggs' in url or 'zbjggg' in url:
        notice_data.notice_type =7
    elif 'cqgzgg' in url:
        notice_data.notice_type =16
    elif 'zgysgg' in url:
        notice_data.notice_type =6
    else:
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:                                                            
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a').text.replace('•','')
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span:nth-child(2)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        
    if notice_data.publish_date is None:
        return
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(7) > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Guangdong Electromechanical Equipment Tendering Center Co., Ltd.'
        customer_details_data.org_parent_id = '7532393'
        customer_details_data.org_email = 'dept2gdmeetc@163.com'
        customer_details_data.org_phone = '020-66341917'
        customer_details_data.org_address = '5th Floor, Dongzhao Building, No. 515, Dongfeng Middle Road, Guangzhou, Guangdong, China Postcode: 510045'
        customer_details_data.org_fax = '020-66341967'
        customer_details_data.postal_code = '510045'
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    url2 = ['https://www.gdebidding.com/zbxxgg/index_',
            'https://www.gdebidding.com/zbyg/index_',
            'https://www.gdebidding.com/zbjggs/index_',
            'https://www.gdebidding.com/zbjggg/index_',
            'https://www.gdebidding.com/cqgzgg/index_']
            #'https://www.gdebidding.com/zgysgg/index_'] 
    
    for item in url2:
        for page_no in range(1,25):
            url= item + str(page_no)+ '.jhtml'
            fn.load_page(page_main, url)
            logging.info('----------------------------------')           
            logging.info(url)

            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.padding-big > div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.padding-big > div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.padding-big > div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
            except:
                logging.info('No new record')
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
