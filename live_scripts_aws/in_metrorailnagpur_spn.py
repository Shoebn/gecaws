from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_metrorailnagpur_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_metrorailnagpur_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_metrorailnagpur_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    
    
    notice_data.notice_url = url
    notice_data.document_type_description = "TENDERS"
    
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(12)').text
        if 'Corrigendum' in notice_type:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass

    try:  
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(10)').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+ [apAP][mM]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d/%m/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:  
        document_opening_time =  tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(11)').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d/%m/%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try: 
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
        try:
            publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date, '%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date, '%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = re.findall('\d+-\d+.\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date, '%d-%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.earnest_money_deposit = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text.split("&")[0].strip()
        document_cost = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text.split("&")[1].strip()
        document_cost = re.sub("[^\d\.\,]","",document_cost)
        notice_data.document_cost =float(document_cost.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(7)').text.split("To")[0]
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try: 
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(7)').text.split("To")[1].replace("\n",'')
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    try: 
        pre_bid_meeting_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount1 = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        numbers = re.findall(r'\d+', est_amount1)
        numbers = [int(num) for num in numbers]
        max_number = max(numbers)
        max_num = str(max_number)
        if 'Crores' in est_amount1 or 'Crore ' in est_amount1 or 'Crs' in est_amount1:
            est_amount= re.findall('\d[\d,\.]*\d|\d',max_num)[0]
            est_amount_replace = est_amount.replace('.','').strip()
            notice_data.est_amount = float(est_amount_replace) * 100000
        else:
            est_amount = re.sub("[^\d\.\,]","",max_num)
            notice_data.est_amount = float(est_amount.replace(',','').strip())
        
        if 'Exclusive of applicable GST' in est_amount1 or 'Excluding' in est_amount1:
            notice_data.netbudgetlc = notice_data.est_amount
        else:
            notice_data.grossbudgetlc = notice_data.est_amount
            
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split("TENDER NOTICE NO :")[1].split("DAT")[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.local_title = local_title.split(publish_date)[1].strip()
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'NAGPUR METRO RAIL PROJECT'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id = "7748165"
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
     
    try:
        for single_records in tender_html_element.find_elements(By.CSS_SELECTOR, ' td:nth-child(1) > a'):
            attachments_data = attachments()
            attachments_data.file_name = single_records.text
            attachments_data.external_url = single_records.get_attribute('href')
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_data: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.metrorailnagpur.com/tenders#fh5co-tab-feature-center1']
    try:
        for url in urls:
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div[2]/div[2]/div[3]/div/div[3]/div/div/section/div/table/tbody[2]/tr')))
            length = len(rows)                                                                              
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div[2]/div[2]/div[3]/div/div[3]/div/div/section/div/table/tbody[2]/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
    except:
        logging.info("No new record")
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
