from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "iq_bocoil_spn"
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
import gec_common.Doc_Download
from webdriver_manager.chrome import ChromeDriverManager


#Note:Fill the captcha to get tender data
#Note: Urban VPN(Israel)

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "iq_bocoil_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
         
    notice_data.script_name = 'iq_bocoil_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IQ'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'IQD'
    
    notice_data.main_language = 'AR'
    
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -If having Extensing date than tack for notice_type 16 and Extension deta "No extension" keyword than tack for notice_type 4
     
    
    # Onsite Field -رقم المناقصة
    # Onsite Comment -Note:If Notice_no "رقم المناقصة" is blank than take from url ,Ref url:"https://boc.oil.gov.iq/index.php?name=monaksa&op=show&id=1454"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -موضوع المناقصة
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -تاريخ الأصدار
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(5)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -تاريخ الغلق
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(6)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -لتفاصيل
    # Onsite Comment -None

    try:                         
        notice_data.notice_url = WebDriverWait(tender_html_element, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(8) > div > a'))).get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:                           
        notice_data.notice_text += WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td.leftblock > center'))).get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    
    try:
        notice_type = page_details.find_element(By.CSS_SELECTOR, ' tr:nth-child(8) > td:nth-child(2)').text
        if "لايوجد تمديد" in notice_type:
            notice_data.notice_type = 4
        else:
            notice_data.notice_type = 16
    except:
        pass
    
# Onsite Field -مرفقات المناقصة
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(9) > td:nth-child(2) > a'):
            attachments_data = attachments()

        # Onsite Field -None
        # Onsite Comment -Note:split the file_name from url

            attachments_data.file_name = single_record.text
        # Onsite Field -None
        # Onsite Comment -Note:Take only file extention from url

            attachments_data.file_type = "pdf"
        
        # Onsite Field -مرفقات المناقصة
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'BASRA OIL COMPANY'
        customer_details_data.org_parent_id = '7525350'
        customer_details_data.org_country = 'IQ'
        customer_details_data.org_language = 'AR'
    # Onsite Field -بريد إتصالِ إلكتروني
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) > td:nth-child(2)').text
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

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)
page_details = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    for i in range(0,50,10):
        url = 'https://boc.oil.gov.iq/index.php?name=monaksa&countpage='+str(i)+'&currenpage=0&all=0'
        fn.load_page(page_main, url, 120)
        fn.load_page(page_details, url, 120)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/center/table[1]/tbody/tr[7]/td/table/tbody/tr/td[2]/table[2]/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/center/table[1]/tbody/tr[7]/td/table/tbody/tr/td[2]/table[2]/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr')))
            length = len(rows)
            
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/center/table[1]/tbody/tr[7]/td/table/tbody/tr/td[2]/table[2]/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
