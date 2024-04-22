from gec_common.gecclass import *
import logging
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sa_nupco"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'sa_nupco'
    notice_data.main_language = 'AR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SA'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'SAR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box.box_arbic  div.box_arbic_col01').text.split("رقم المنافسة")[1].replace('\n','')
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > p:nth-child(2)').text  
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.column-box.mix div > a').get_attribute("href") 
        logging.info(notice_data.notice_url)                    
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.right.paddingright').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "div.right.paddingright > div:nth-child(2) > p").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
    except:
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m-%d-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass
    notice_data.publish_date = date.today().strftime('%Y/%m/%d %H:%M:%S')
    logging.info(notice_data.publish_date)
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    

    try:
        document_opening_time = page_details.find_element(By.CSS_SELECTOR, 'div.right.paddingright > div:nth-child(3) > p').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
    except:
        try:
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m-%d-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
                pass
    
    try:
        notice_data.document_fee = page_details.find_element(By.CSS_SELECTOR, 'div.right.paddingright > div:nth-child(4) > p').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'NATIONAL UNIFIED PROCUREMENT COMPANY (NUPCO)'
        customer_details_data.org_parent_id = 7700088
        customer_details_data.org_address = 'Saeed Al Salami Street,DigitalCity Riyadh 12251 – 2721Kingdom of Saudi Arabia'
        customer_details_data.org_phone = '+920018184 966'
        customer_details_data.org_country='SA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.btn_wrap_Tender > ul > li:nth-child(n)'):
            external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            if 'pdf' in external_url or 'PDF' in external_url or 'doc' in external_url or 'xml' in external_url or 'xmls' in external_url:
                attachments_data = attachments()
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
                attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(attachments_data.file_name) 
                attachments_data.file_description = attachments_data.file_name 
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            
                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('.')[-1]
                except Exception as e:
                    logging.info("Exception in external_url: {}".format(type(e).__name__))
                    pass
            
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://nupco.com/%d8%a7%d9%84%d9%85%d9%86%d8%a7%d9%81%d8%b3%d8%a7%d8%aa/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Container"]/div')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Container"]/div')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    logging.info("Exception:"+str(e))
    raise e
    
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
