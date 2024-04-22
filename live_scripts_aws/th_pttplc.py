from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "th_pttplc"
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
SCRIPT_NAME = "th_pttplc"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'th_pttplc'
    
    notice_data.main_language = 'TH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'THB'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > a > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > a > h2').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'h3.title-announce').text.split('เลขที่ประกาศ')[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " div:nth-child(5) > div.col-lg-12.float-left.title-announce2").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        try:
            publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
            
        except:
            try:
                publish_date = re.findall('\d+ \w+\. \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
                
            except:
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " div:nth-child(4) > div.col-lg-12.float-left.title-announce2").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        try:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[1]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\d+ \w+\. \d{4}',notice_deadline)[1]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = float(tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-5.float-left.title-announce2').text)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.est_amount = float(tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-5.float-left.title-announce2').text)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass


    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.container.box-announce-desktop > h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass        
 
    notice_data.notice_url = 'https://procurement.pttplc.com/th/Invitation'
    
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.container > div:nth-child(2) > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    
    try:              
        customer_details_data = customer_details()

        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text.split('หน่วยงานจัดหา: ')[1].split("\n")[0]
        customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
       
        customer_details_data.org_country = 'TH'
        customer_details_data.org_language = 'TH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:              
        external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body2.body-announce a')
        page_main.execute_script("arguments[0].click();",external_url)
        time.sleep(2)
        external_urls = tender_html_element.find_elements(By.CSS_SELECTOR,'div.box-announce-desktop a')
        
        for ex_url in external_urls:
            attachments_data = attachments()
            attachments_data.external_url = ex_url.get_attribute('href')
            attachments_data.file_type = 'pdf'
            file_name = tender_html_element.find_element(By.CSS_SELECTOR,'div.box-announce-desktop table tbody tr:nth-child(1) td:nth-child(2)').get_attribute('innerHTML')
            attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(file_name)
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
    urls = ['https://procurement.pttplc.com/th/Invitation'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Table"]/div[2]')))

        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Table"]/div[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#Table > div.container-fluid.box-announce-mobile > div:nth-child(2) > div.card.card-announce')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#Table > div.container-fluid.box-announce-mobile > div:nth-child(2) > div.card.card-announce')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.WidelyTable-Page.btn ')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Table"]/div[1]/div[1]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
    