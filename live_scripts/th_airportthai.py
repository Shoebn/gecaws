from gec_common.gecclass import *
import logging
import jsons
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
SCRIPT_NAME = "th_airportthai"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.main_language = 'TH'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'THB'

    notice_data.procurement_method = 2

    
    notice_data.script_name = "th_airportthai"
    notice_data.notice_url =url
    
    # Onsite Field -Display Date
    # Onsite Comment -None
    
    try:
        document_type_description = page_main.find_element(By.CSS_SELECTOR, '#container > div.container.navi-space > div').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span:nth-child(3)").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date).split(':')[1]
        try:
            notice_data.publish_date = datetime.strptime(publish_date,' %d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.publish_date = datetime.strptime(publish_date,' %d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    logging.info(notice_data.publish_date)
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    if 'วันที่ยื่นข้อเสนอ : ' in tender_html_element.text:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > span:nth-child(5)").text
            notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline).split(':')[1]
            try:
                notice_data.notice_deadline = datetime.strptime(notice_deadline,' %d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_data.notice_deadline = datetime.strptime(notice_deadline,' %d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
            
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
    else:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > span:nth-child(7) > font").text
            notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline).split(':')[1]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,' %d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > strong').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    if 'ไม่พบข้อมูล' in notice_data.local_title:
        return
    
    if 'cancel' in notice_data.notice_title or 'Cancellation of' in notice_data.notice_title:
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 4
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')                    
    except:
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'AIRPORTS OF THAILAND PUBLIC CO LTD'
        customer_details_data.org_language = 'TH'
        customer_details_data.org_country = 'TH'
        customer_details_data.org_parent_id = '7548547'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'a.download_file'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.file_name = single_record.text
            attachments_data.file_name  = GoogleTranslator(source='auto', target='en').translate(attachments_data.file_name )
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://aotdatainfo.airportthai.co.th/Category/index/158", "https://aotdatainfo.airportthai.co.th/bidding/Category/index/133", "https://aotdatainfo.airportthai.co.th/bidding/Category/index/158", "https://aotdatainfo.airportthai.co.th/bidding/Category/index/159", "https://aotdatainfo.airportthai.co.th/bidding/Category/index/161"] 
    for url in urls:
        fn.load_page(page_main, url, 180)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk=WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="acceptCookies"]'))).click()
        except:
            pass
        
        for page_no in range(2,3):
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container"]/div[4]/div[2]/div[2]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container"]/div[4]/div[2]/div[2]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container"]/div[4]/div[2]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 180).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="container"]/div[4]/div[2]/div[2]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
                
            except:
                logging.info("No new record")
                pass
                
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)