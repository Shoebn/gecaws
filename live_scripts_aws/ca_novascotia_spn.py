
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_novascotia_spn"
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
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.common.keys import Keys


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_novascotia_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_novascotia_spn'
    notice_data.currency = 'CAD'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'EN'
    notice_data.notice_type = 4
    notice_data.procurement_method = 2
    
    notice_type = tender_html_element.find_element(By.CSS_SELECTOR, "td.p-0  td:nth-child(7)").text
    if notice_type=='OPEN':
        notice_data.notice_type = 4
    else:
        notice_data.notice_type = 16

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.p-0  td:nth-child(5)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.p-0  td:nth-child(6)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td.p-0  td:nth-child(2)').text 
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.p-0  td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.p-0  td:nth-child(1) > a').get_attribute("href")            
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.p-0  td:nth-child(1)').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('tenders/')[1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass    

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::p[1]").text  
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Category')]//following::span[11]").text  
        if 'Goods' in notice_contract_type or 'Construction' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Works' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Services'
        elif 'construction' in notice_contract_type:
            notice_data.notice_contract_type = 'Works' 
        elif 'Dental Supplies' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply' 
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Category')]//following::span[11]").text  
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        contract_duration_1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Duration')]").text.split('Contract ')[1]  
        contract_duration_2 = page_details.find_element(By.XPATH, "//*[contains(text(),'Duration')]//following::p[1]").text
        notice_data.contract_duration = contract_duration_1+' '+contract_duration_2
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div:nth-child(2) > div.col-lg-9').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.issuer-col').text

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Contact Name')]//following::p[1]").text  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Contact Method')]//following::p[1]").text 
            customer_details_data.org_email = org_email.split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        try:
            org_phone  = page_details.find_element(By.XPATH, "//*[contains(text(),'Contact Method')]//following::span[1]").text 
            if len(org_phone)> 7:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'EN'

        try: 
            customer_details_data.org_address  = page_details.find_element(By.XPATH, "//*[contains(text(),'Procurement Entity')]//following::p[2]").text 
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tender-detail__row > div > div:nth-child(2) > div > div'): 
            
            attachments_data = attachments()

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, "div > span:nth-child(2) > a").get_attribute('href') 
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, "div > div > span:nth-child(2) > a").text  

            try:
                file_type = attachments_data.file_name.split('.')[-1]
                if len(file_type)<5:
                    attachments_data.file_type = file_type
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        show_all_comodities_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main"]/div[2]/div[2]/div/div[1]/div/div[1]/div[6]/button'))).click()    
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in show_all_comodities_click: {}".format(type(e).__name__)) 
        pass  

    try:           
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tender-detail__row'):
            if 'Commodity Level ' in single_record.text:
                
                for single_record_1 in single_record.find_elements(By.CSS_SELECTOR, 'div > div')[1:]:
        
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number
                    lot_details_data.lot_title = single_record_1.find_element(By.CSS_SELECTOR, 'p').text
                    
                    if '–' not in lot_details_data.lot_title:
                        lot_details_data.lot_actual_number = single_record_1.find_element(By.CSS_SELECTOR, 'h4').text
                        contract_type = single_record.find_element(By.CSS_SELECTOR, 'h4:nth-child(2)').text.split('Category:')[1].strip() 
                        if 'Goods' in contract_type or 'Construction' in contract_type:
                            lot_details_data.contract_type = 'Supply'
                        elif 'Works' in contract_type:
                            lot_details_data.contract_type = 'Works'
                        elif 'Services' in contract_type:
                            lot_details_data.contract_type = 'Services'
                        elif 'construction' in contract_type:
                            lot_details_data.contract_type = 'Works'                
                        elif 'Dental Supplies' in contract_type:
                            lot_details_data.contract_type = 'Supply'                             
                        lot_details_data.lot_contract_type_actual = contract_type

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number+=1

    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass    
    
 #-----------------------------------------------------

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://procurement-portal.novascotia.ca/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        status_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="filterStatus"]/div[1]/div[2]/div'))).click()    
        time.sleep(5)

        action = ActionChains(page_main) 

        for click in range(1,5):
            action.send_keys(Keys.ENTER) 
        time.sleep(5)
        action.perform() 
        time.sleep(10)
        
        remove_award_click = page_main.find_element(By.XPATH,'//*[@id="filterStatus"]/div[1]/div[1]/div[2]/div[2]').click()   
        time.sleep(5)
        remove_expired_click = page_main.find_element(By.XPATH,'//*[@id="filterStatus"]/div[1]/div[1]/div[3]/div[2]').click()   
        time.sleep(5)
        apply_filter_click = page_main.find_element(By.XPATH,'//*[@id="main"]/div[2]/div[1]/div[1]/div/div/button').click()   
        time.sleep(5)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main"]/div[2]/div[2]/div/div[1]/div/div/div/div[2]/div/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/div[2]/div/div[1]/div/div/div/div[2]/div/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/div[2]/div/div[1]/div/div/div/div[2]/div/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
            
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,f'ol > li:nth-child({page_no})> button')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(5)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main"]/div[2]/div[2]/div/div[1]/div/div/div/div[2]/div/div/table/tbody/tr'),page_check))
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
    
