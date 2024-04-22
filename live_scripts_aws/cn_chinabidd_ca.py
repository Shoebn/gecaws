#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_chinabidd_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_chinabidd_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'cn_chinabidd_ca'
    
    notice_data.main_language = 'ZH'
    
    notice_data.currency = 'CNY'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
   
    notice_data.document_type_description = "Bid Winning Announcement"
    
    # Onsite Field -编 号 --- serial number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -
    # Onsite Comment -split notice_no.here "http://www.chinabidding.org.cn/BidInfoDetails.aspx?bid=21573125&type=2023" grab only "21573125".

    # Onsite Field -日 期 --- date
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "span#cphMain_tm").text
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
            publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        if notice_data.notice_no == None:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href").split('bid=')[1].split('&type')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no1: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.doutline').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")

    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, '#cphMain_tle').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -industry
    # Onsite Comment -None
    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"所属行业:")]//following::td[1]').text.strip()
        category = GoogleTranslator(source='auto', target='en').translate(notice_data.category)
        cpv_codes = fn.CPV_mapping("assets/cn_chinabidd_ca_category.csv",category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'China Government Procurement Bidding Network'
        customer_details_data.org_parent_id = '7782735'
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'

        # Onsite Field -所在地区:
        # Onsite Comment -None

        try:
            customer_details_data.org_state = page_details.find_element(By.XPATH, '//*[contains(text(),"所在地区:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -
        # Onsite Comment -split after "供应商邮箱:".just grab "zfcgzb@gov-cg.org.cn"

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"详情咨询电话:")]//following::td[1]').text
            email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
            customer_details_data.org_email = email_regex.findall(org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -
        # Onsite Comment -split after "客服".

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"详情咨询电话:")]//following::td[1]').text.split('客服')[1].split('(中国政府采购招标网)')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://www.chinabidding.org.cn/LuceneSearch.aspx?kwd=&filter=b3-0-0-keyword-7"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,200):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="TableList"]/tbody/tr[3]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="TableList"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length,2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="TableList"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"下一页")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="TableList"]/tbody/tr[3]'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
