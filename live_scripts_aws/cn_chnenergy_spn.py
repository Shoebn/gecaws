from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_chnenergy_spn"
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
SCRIPT_NAME = "cn_chnenergy_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'cn_chnenergy_spn'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'CNY'
   
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 4
  
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "ul.right-items > li> span").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(2)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.container.mt20 > div.row').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -split first date as a document_purchase_start_date             ref_url : "http://www.chnenergybidding.com.cn/bidweb/001/001002/001002001/20231102/59652725-c07d-42f3-91bf-c7c82ef6975b.html"

    try:
        document_purchase_start_time = page_details.find_element(By.XPATH, '//*[contains(text(),"4.3")]').text.split(",")[0].strip()
        document_purchase_start_time = re.findall('\d{4}-\d+-\d+',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%Y-%m-%d').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split second date as a document_purchase_end_date             ref_url : "http://www.chnenergybidding.com.cn/bidweb/001/001002/001002001/20231102/59652725-c07d-42f3-91bf-c7c82ef6975b.html"

    try:
        document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),"4.3")]').text.split("，")[1].strip()
        document_purchase_end_time = re.findall('\d{4}-\d+-\d+',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%Y-%m-%d').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -ref_url : "http://www.chnenergybidding.com.cn/bidweb/001/001002/001002001/20231102/59652725-c07d-42f3-91bf-c7c82ef6975b.html"

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        
        # Onsite Field -招 标 人：
        # Onsite Comment -split the data after "招 标 人："   , ref_url : "http://www.chnenergybidding.com.cn/bidweb/001/001002/001002003/20231102/ef550b94-3e45-4ca6-924d-e8b73bd5793b.html"

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"9.联系方式")]//following::p[1]').text.split("：")[1].strip()

        # Onsite Field -地    址
        # Onsite Comment -split the data after "  地    址："   ,   ref_url :"http://www.chnenergybidding.com.cn/bidweb/001/001002/001002003/20231102/ef550b94-3e45-4ca6-924d-e8b73bd5793b.html"

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"9.联系方式")]//following::p[2]').text.split("：")[1].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        # Onsite Field -邮    编：
        # Onsite Comment -split the data after " 邮    编："   ,   ref_url :"http://www.chnenergybidding.com.cn/bidweb/001/001002/001002003/20231102/ef550b94-3e45-4ca6-924d-e8b73bd5793b.html"

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"9.联系方式")]//following::p[3]').text.split("：")[1].strip()
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -联 系 人：
    # Onsite Comment -split the data after "  联 系 人："   ,   ref_url :"http://www.chnenergybidding.com.cn/bidweb/001/001002/001002003/20231102/ef550b94-3e45-4ca6-924d-e8b73bd5793b.html"

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"9.联系方式")]//following::p[4]').text.split("：")[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -电    话：
        # Onsite Comment -split the data after "电    话："   ,   ref_url :"http://www.chnenergybidding.com.cn/bidweb/001/001002/001002003/20231102/ef550b94-3e45-4ca6-924d-e8b73bd5793b.html"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"9.联系方式")]//following::p[5]').text.split("：")[1].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -电子邮箱：
    # Onsite Comment -split the data after " 电子邮箱："   ,   ref_url :"http://www.chnenergybidding.com.cn/bidweb/001/001002/001002003/20231102/ef550b94-3e45-4ca6-924d-e8b73bd5793b.html"

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"9.联系方式")]//following::p[6]').text.split("：")[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["http://www.chnenergybidding.com.cn/bidweb/001/001002/moreinfo.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div[2]/div[2]/ul[1]/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div[2]/div[2]/ul[1]/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div[2]/div[2]/ul[1]/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div/div[2]/div[2]/ul[1]/li'),page_check))
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
