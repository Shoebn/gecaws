import time
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
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uy_uruguayconcursa_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = "uy_uruguayconcursa_spn"
    
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UY'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'UYI'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2) span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) span > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass  
    
    try:
        publish_date =tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) span').text
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_deadline =tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) span').text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(4) span > a').get_attribute('href')         
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
        
    try:
        text1 = page_details.find_element(By.XPATH,'/html/body/form/div[1]/div[2]/div/div[2]/div[2]/fieldset').text
    except:
        pass
        
    try:
        notice_data.local_description =re.findall(r'Descripción de Función:\s*(.*?)\n',text1)[0]
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'UY'
        customer_details_data.org_language = 'ES'
        
        org_name = re.findall(r'Organismo y Cantidad de Puestos\s*(.*?)\n',text1)[0]
        if 'Puesto(s)' in org_name:
            customer_details_data.org_name = re.sub(r"s*\d+\s*Puesto\(s\)\s*","",org_name)
        else:
            customer_details_data.org_name = org_name
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass       
    try:              
        attachments_data = attachments()
        try:
            attachments_data.file_name = page_details.find_element(By.XPATH, '//*[@id="TXTDOCUMENTO_0001"]').text
        except Exception as e:
            logging.info("Exception in file_name: {}".format(type(e).__name__))
            pass
    
        external_url = page_details.find_element(By.XPATH, '//*[@id="TXTDOCUMENTO_0001"]/a')
        page_details.execute_script("arguments[0].click();",external_url)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
    
        try:
            attachments_data.file_type =attachments_data.external_url.split('.')[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/form/div[1]/div[2]/div/div[2]/div[2]/fieldset').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    notice_data.identifier =  str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://www.uruguayconcursa.gub.uy/Portal/servlet/com.si.recsel.inicio"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,16):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div/div[2]/div/div[2]/div[2]/fieldset[2]/strong/table/tbody/tr[6]/td/div/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div/div[2]/div/div[2]/div[2]/fieldset[2]/strong/table/tbody/tr[6]/td/div/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div/div[2]/div/div[2]/div[2]/fieldset[2]/strong/table/tbody/tr[6]/td/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break

            try:   
                next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="NEXT"]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                time.sleep(5)
                page_check2 = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div/div[2]/div/div[2]/div[2]/fieldset[2]/strong/table/tbody/tr[6]/td/div/table/tbody/tr[2]'))).text
                WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.XPATH, '/html/body/form/div/div[2]/div/div[2]/div[2]/fieldset[2]/strong/table/tbody/tr[6]/td/div/table/tbody/tr[2]'),page_check))
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
