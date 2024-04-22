from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_dafs"
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
SCRIPT_NAME = "us_dafs"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'us_dafs'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'USD'
   
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
        
    notice_data.notice_url = url
    
    try:
        skip_rows = tender_html_element.text
        if "Date Posted" in skip_rows:
            return
    except:
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-rfp-status').text
        if "Awarded" in notice_data.document_type_description:
            notice_data.notice_type = 7
            notice_data.script_name = 'us_dafs_ca'
        elif "Cancelled" in notice_data.document_type_description or "Closed - Evaluation of Proposals" in notice_data.document_type_description:
            notice_data.notice_type = 16
            notice_data.script_name = 'us_dafs_amd'
        else:
            notice_data.notice_type = 4
            notice_data.script_name = 'us_dafs_spn'
    except:
        try:
            notice_data.notice_type = 4
            notice_data.script_name = 'us_dafs_spn'
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-rfp-').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        if len(notice_data.local_title) < 5:
            return
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        if notice_data.notice_type != 7:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        if notice_data.notice_type != 7:
            notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
            try:
                notice_deadline_date = re.findall('\w+ \d+, \d{4}',notice_deadline1)[0]
                notice_deadline_time = re.findall('\d+:\d+',notice_deadline1)[0]
                notice_deadline = notice_deadline_date+' '+notice_deadline_time
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except:
                try:
                    notice_deadline_date = re.findall('\w+ \d+. \d{4}',notice_deadline1)[0]
                    notice_deadline_time = re.findall('\d+:\d+',notice_deadline1)[0]
                    notice_deadline = notice_deadline_date+' '+notice_deadline_time
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d. %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                    logging.info(notice_data.notice_deadline)
                except:
                    try:
                        notice_deadline_date = re.findall('\w+ \d+ \d{4}',notice_deadline1)[0]
                        notice_deadline_time = re.findall('\d+:\d+',notice_deadline1)[0]
                        notice_deadline = notice_deadline_date+' '+notice_deadline_time
                        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                        logging.info(notice_data.notice_deadline)
                    except:
                        pass
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        customer_details_data.org_name = fn.procedure_mapping("assets/us_dafs_org.csv",org_name)
        if customer_details_data.org_name is None:
            customer_details_data.org_name = org_name

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, "td:nth-child(1) > a"):
            attachments_data = attachments()
            
            attachments_data.external_url = single_record.get_attribute("href")
            
            attachments_data.file_name = single_record.text

            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type_1: {}".format(type(e).__name__))
                pass

            if attachments_data.external_url != '':
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
        pass
    
    try:
        if notice_data.notice_type == 7 or notice_data.notice_type == 16:
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, "td:nth-child(5) > span > a"):
                attachments_data = attachments()

                attachments_data.external_url = single_record.get_attribute("href")

                attachments_data.file_name = single_record.text

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type_2: {}".format(type(e).__name__))
                    pass

                if attachments_data.external_url != '':
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
        pass
    
    try:
        if notice_data.notice_type == 7:
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, " td:nth-child(8) > span > a"):
                attachments_data = attachments()

                attachments_data.external_url = single_record.get_attribute("href")

                attachments_data.file_name = single_record.text

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type_3: {}".format(type(e).__name__))
                    pass

                if attachments_data.external_url != '':
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_3: {}".format(type(e).__name__)) 
        pass
    
    try:
        if notice_data.notice_type == 7:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1

            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english = notice_data.notice_title

            award_details_data = award_details()
            
            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
            
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

            if lot_details_data.award_details != []:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    data_final = output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.maine.gov/dafs/bbm/procurementservices/vendors/rfps"] 
    for url in urls:
        fn.load_page(page_main, url, 60)
        logging.info('----------------------------------')
        logging.info(url)
            
        for page_no in range(2,4):#4
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody > tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))
            length = len(rows)
            for records in range(0,length-1):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                    
            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"Next")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tbody > tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()    
    output_json_file.copyFinalJSONToServer(output_json_folder)