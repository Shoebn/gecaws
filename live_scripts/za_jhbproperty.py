from gec_common.gecclass import *
import logging
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
SCRIPT_NAME = "za_jhbproperty"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'za_jhbproperty_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
    notice_data.main_language = 'EN'
    notice_data.currency = 'INR'
    notice_data.procurement_method = 2
    notice_data.currency = 'ZAR'
    
    if url==urls[2]:
        notice_data.notice_type = 7
        notice_data.script_name = 'za_jhbproperty_ca'
    else:
        notice_data.notice_type = 4
        notice_data.script_name = 'za_jhbproperty_spn'
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass
        
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name ="City of Joburg Property Company SOC Ltd."
        customer_details_data.org_email ="clientservicingunit@jhbproperty.co.za"
        customer_details_data.org_fax ="+27 10 219 9000"
        customer_details_data.org_phone ="+27 10 219 9400"
        customer_details_data.org_parent_id =7804896
        customer_details_data.org_address =  "P.O Box 31565,Braamfontein,2017"
        customer_details_data.org_website ="www.jhbproperty.co.za"
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        if url==urls[0]:
            notice_data.document_type_description = "Request For Quotations (RFQs)"
        if url==urls[1]:
            notice_data.document_type_description = "Request For Proposals (RFPs)"
        if url==urls[2]:
            notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        pass    
    

    if url!=urls[2]:
        try:
            date1=tender_html_element.find_element(By.CSS_SELECTOR, 'td.col-date.nowrap.sorting_1').text
            notice_data.publish_date = datetime.strptime(date1,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except:
            pass
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
    else:
        try:
            date1=tender_html_element.find_element(By.CSS_SELECTOR, 'td.col-published_date').text
            notice_data.publish_date = datetime.strptime(date1,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date) 
        except:
            pass
         
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) a').get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        try: 
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > span:nth-child(n)  a')[:-2]:
                attachments_data = attachments()
                attachments_data.file_name = single_record.text
                if 'Back to:' in attachments_data.file_name:
                    pass
                attachments_data.external_url=single_record.get_attribute('href')

                attachments_data.file_type =attachments_data.external_url.split('.')[-1] 
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)

        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        if url==urls[2]:
            try:
                lot_details_data = lot_details()
                lot_details_data.lot_number=1
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
                award_details_data = award_details()
                award_details_data.bidder_name=page_details.find_element(By.XPATH, "//*[contains(text(),'Name Of Awarded Bidder:')]")#.split('Name Of Awarded Bidder: ')[1]
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
            except:
                pass
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        try:
            notice_data.notice_text +=page_details.find_element(By.XPATH,'//*[@id="content"]').get_attribute('innerHTML')
        except:
            pass
    except:
        pass
    

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver() 
page_details = fn.init_chrome_driver() 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://jhbproperty.co.za/supply-chain-management-scm/rfqs/","https://jhbproperty.co.za/supply-chain-management-scm/rfps/",
           "https://jhbproperty.co.za/supply-chain-management-scm/awarded-bids/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        time.sleep(2)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tbody tr'),page_check))
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
