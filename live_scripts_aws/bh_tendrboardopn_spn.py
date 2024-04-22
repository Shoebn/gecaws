from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bh_tendrboardopn_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bh_tendrboardopn_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'bh_tendrboardopn_spn'
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BHD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > a > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > a').text.split(notice_data.notice_no)[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(6)').text
    except:
        pass

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4)').text
        notice_deadline = re.findall('\d+ \w+,\d{4}',notice_deadline)[0]
        notice_deadline1 = datetime.strptime(notice_deadline,'%d %b,%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '.resultstable > div a').get_attribute("href") 
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        logging.info(notice_data.notice_url)
        fn.load_page(page_details,notice_data.notice_url,180)
        WebDriverWait(page_details, 120).until(EC.presence_of_element_located((By.XPATH,'//*[@id="page"]/section[2]/div/div/div/div[1]/div/dl'))).text
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    try:
        page_doesnt_exist = page_details.find_element(By.CSS_SELECTOR,'#page > section.no-padding.sh-company-history > div > div > div > div:nth-child(1) > h3').text
        if '404' in page_doesnt_exist:
            notice_data.notice_deadline = notice_deadline1
    except:
        pass     
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.tender-details > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    
    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Opening Date")]//following::dd[1]').text
        document_opening_time = re.findall('\d+ \w+ \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %B %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"Initial Bond")]//following::dd[1]').text.split(' ')[1]
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        document_cost = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Fees")]//following::dd[1]').text.split(' ')[1]
        notice_data.document_cost = float(document_cost)
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        if('<' in notice_data.notice_no):
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Number:")]//following::span').text
        else:
            notice_data.notice_no = notice_data.notice_no
    except:
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Number:")]//following::span').text
    except:
        pass
    
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Duration")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try: 
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Publish Date')]//following::dd[1]").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Closing Date')]//following::dd[1]").text
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section.tender-details > div'):
            customer_details_data = customer_details()

            customer_details_data.org_name = org_name

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"Inquiries")]//following::strong[2]').text
            except Exception as e: 
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'BH'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        attachments_data = attachments()
        attachments_data.file_type = "PDF"
        attachments_data.file_name = "Download"

        external_url = page_details.find_element(By.CSS_SELECTOR, 'div.downloadpdf a')
        page_details.execute_script("arguments[0].click();",external_url)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])


        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass   

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_details = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenderboard.gov.bh/Tenders/To%20be%20Opened/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#cphBaseBody_CphInnerBody_TenderDetailsBlock > div.rows'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#cphBaseBody_CphInnerBody_TenderDetailsBlock > div.rows')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#cphBaseBody_CphInnerBody_TenderDetailsBlock > div.rows')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
        
                try:   
                    next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check1 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#cphBaseBody_CphInnerBody_TenderDetailsBlock > div.rows'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#cphBaseBody_CphInnerBody_TenderDetailsBlock > div.rows'),page_check))
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
