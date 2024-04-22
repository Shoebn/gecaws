from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sa_etimadav"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sa_etimadav"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'sa_etimadav'
    notice_data.main_language = 'AR'
    notice_data.currency = 'SAR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SA'
    notice_data.performance_country.append(performance_country_data)    
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
  
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div > div > div:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div > div > div:nth-child(5)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > div > div:nth-child(3)').text.split('مدة الإعلان عن المنافسة')[1]
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_url = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > div:nth-child(4) > p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
        
 
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'الرقم المرجعى للإعلان')]//following::span[1]").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    try:
        notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),'تعريف عن المنافسة')]//following::span[1]").text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#d-1 > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
        
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'تعريف عن المنافسة')]//following::span[1]").text
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[@id="d-1"]/div/div/div/div/div/div[2]/div/ul/li[6]/div/div[2]').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
    try:
        document_type_description = page_details.find_element(By.XPATH, "//*[contains(text(),'نوع المنافسة')]//following::span[1]").text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#d-1 > div'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'SA'

            try:
                customer_details_data.org_name = single_record.find_element(By.XPATH, "//*[contains(text(),'اسم الجهة')]//following::span[1]").text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_description = single_record.find_element(By.XPATH, "//*[contains(text(),'اسم الفرع')]//following::span[1]").text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
       
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        try:
            lot_title = single_record.find_element(By.XPATH, "//*[contains(text(),'اسم الإعلان')]//following::span[1]").text
            lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
            lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_title)
        except:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
            lot_details_data.lot_description = notice_data.notice_title

        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
       
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = [' https://tenders.etimad.sa/Announcement/AllVisitorAnnouncements'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="cardsresult"]/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="cardsresult"]/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="cardsresult"]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="cardsresult"]/div[1]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    logging.info("Exception:"+str(e))
    raise e
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
