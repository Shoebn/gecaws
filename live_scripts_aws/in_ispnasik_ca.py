from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_ispnasik_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_ispnasik_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'

    notice_data.script_name = 'in_ispnasik_ca'
    
    notice_data.notice_type = 7
    notice_data.procurment_method = 2
    
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').get_attribute('text')
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__)) 
        pass 
        
    notice_data.document_type_description = 'Awarded Tenders'
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(8) a').get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass    
   
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
       
    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
        notice_data.publish_date = datetime.strptime(publish_date, '%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    logging.info(notice_data.publish_date)
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_text1 = page_details.find_element(By.XPATH,'/html/body/div/div[2]/div/div/main/article/div/div/div').text
    except:
        pass
    try:
        notice_data.local_description = re.findall(r'Nature of work : (.+?)\n',notice_text1)[0]
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__)) 
        pass        
    try:
        notice_data.notice_no = re.findall(r'Contract No :\n(.+?)\n',notice_text1)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass 
    try:
        lot_number = 1
        lot_details_data=lot_details()
        lot_details_data.lot_number = lot_number
        lot_details_data.lot_title = notice_data.local_title
        award_details_data = award_details()
        award_details_data.bidder_name = re.findall(r'Name of Contractor :\n(.+?)\n',notice_text1)[0]
        try:
            award_date = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(5)').text
            award_details_data.award_date = datetime.strptime(award_date, '%Y-%m-%d').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in award_date: {}".format(type(e).__name__)) 
            pass
        try:
            grossawardvaluelc = re.findall(r'Value of Contract :\n(.+?)\n',notice_text1)[0]
            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
            grossawardvaluelc = grossawardvaluelc.replace(',','').replace('.','').strip()
            award_details_data.grossawardvaluelc = float(grossawardvaluelc)
        except Exception as e:
            logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__)) 
            pass
        
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
        lot_number +=1
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'INDIA SECURITY PRESS'
        customer_details_data.org_parent_id = '7549220'
        try:
            customer_details_data.org_address =tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__)) 
            pass            
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH,'/html/body/div/div[2]/div/div/main/article/div/div/div').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    urls = ['https://ispnasik.spmcil.com/en/awarded-tenders/'] 

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
            
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, ' /html/body/div[1]/div[2]/div/div/main/article/div/div/div/table/tbody/tr')))
            length = len(rows) 
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/main/article/div/div/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        except:
            logging.info("No new record")
            break 

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)