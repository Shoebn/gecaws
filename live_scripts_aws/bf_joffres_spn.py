from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bf_joffres_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from selenium import webdriver
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bf_joffres_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'bf_joffres_spn'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BF'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'BHD'
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div > div.d-inline > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " small.expire-date.text-success").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' div > div.d-inline > a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > main > div.job-post-company.pt-40.pb-50').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference Number")]//parent::span[1]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.category = page_details.find_element(By.XPATH, '''//*[contains(text(),"Domaine de l'appe")]//following::span[1]''').text
        except:
            try:
                category1 = page_details.find_element(By.XPATH, '''//*[contains(text(),"Domaines de l'appe")]//following::span[1]''').text
                category2 = page_details.find_element(By.XPATH, '''//*[contains(text(),"Domaines de l'appe")]//following::span[2]''').text
                notice_data.category = category1+'|'+category2
            except Exception as e:
                logging.info("Exception in category: {}".format(type(e).__name__)) 
                pass 
        
        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Catégorie")]//following::span[1]').text
            if 'Biens' in  notice_data.contract_type_actual or 'Biens et service' in  notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply' 
            elif 'Services' in  notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__)) 
            pass  
        
        try:
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publié-le")]//following::span[1]').text
            publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'BF'
            customer_details_data.org_language = 'FR'
            customer_details_data.org_name = 'JOFFRES'
            customer_details_data.org_parent_id = 7814757
            customer_details_data.org_address = "Rue Weem Doogo, Wemtenga, Ouagadougou, Burkina Faso"
            
            try:
                org_phone = page_details.find_element(By.CSS_SELECTOR, '''body > main > div.job-post-company.pt-40.pb-50 > div > div > div.col-md-8.col-lg-8 > div > div''').text
                if 'Tél:' in org_phone:
                    customer_details_data.org_phone = org_phone.split('Tél:')[1].split('-  E-mail:')[0].strip()
                else:
                    customer_details_data.org_phone = '00226 02 45 07 07'
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                pass 
            
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '''//*[contains(text(),"Contact : Unité achat")]//following::span[1]''').text
            except:
                try:
                    org_email = page_details.find_element(By.CSS_SELECTOR, '''body > main > div.job-post-company.pt-40.pb-50 > div > div > div.col-md-8.col-lg-8 > div > div''').text
                    if 'E-mail:' in org_email:
                        customer_details_data.org_email = org_email.split('E-mail:')[1].strip()
                    else:
                        customer_details_data.org_email = 'joffres@jofedigital.com'
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                    pass             
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try:
            lot_data = page_details.find_element(By.CSS_SELECTOR, '''body > main > div.job-post-company.pt-40.pb-50 > div > div > div.col-md-8.col-lg-8 > div > div''').text
            if '- Lot' in lot_data:
                data = lot_data.split('- Lot')
                lot_number = 1
                for single_record in data[1:]:
                    lot_details_data = lot_details() 
                    lot_details_data.lot_number = lot_number
                    
                    lot_details_data.lot_title = single_record.split(':')[1].split('\n')[0].strip()
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
            elif 'LOT ' in lot_data:
                data = lot_data.split('LOT ')
                lot_number = 1
                for single_record in data[1:]:
                    lot_details_data = lot_details() 
                    lot_details_data.lot_number = lot_number
                    
                    lot_details_data.lot_title = single_record.split(':')[1].split('\n')[0].strip()
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details =fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.joffres.net/appel-offres-priv%C3%A9s"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url) 
            
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.job'))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.job')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.job')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//*[@class='page-link'])[last()]")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.job'),page_check))
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
