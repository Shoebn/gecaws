from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_purcosa_spn"
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
SCRIPT_NAME = "za_purcosa_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'NOK'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.script_name = "za_purcosa_spn"
    
    notice_data.notice_type = 4
          
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-member-tender-number').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, "td.views-field.views-field-field-purchase-deadline").text
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time : {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-categories-extra').text
        category_name = notice_data.category.lower()
        cpv_codes_list = fn.CPV_mapping("assets/za_purcosa_spn_procedure.csv",category_name)
        for each_cpv in cpv_codes_list:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = each_cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "td.views-field.views-field-title a").get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.panel-body').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:  
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#description > a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text.split(".")[0].strip()

            attachments_data.external_url = single_record.get_attribute('href')
            
            try:
                attachments_data.file_type = single_record.text.split(".")[-1].strip()
            except:
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '(//*[contains(text(),"Submission deadline:")])//following::span[1]').text
        notice_deadline = re.findall('\d+ \w+, \d{4} - \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B, %Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR,"  div.panel-body > ul > li:nth-child(3) > a").click()
        time.sleep(3)
    except:
        pass
    
    try:
        document_cost = page_details.find_element(By.XPATH, '(//*[contains(text(),"Fee payable to PURCO ")])[1]//following::div[1]').text
        document_cost = re.sub("[^\d+]",'',document_cost)
        notice_data.document_cost = float(document_cost.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR,"  div.panel-body > ul > li:nth-child(4) > a").click()
        time.sleep(3)
    except:
        pass
            
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "PURCHASING CONSORTIUM SOUTHERN AFRICA NPC"
        
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-members').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
            
        try:
            contact_person = ''
            for single_record in page_details.find_elements(By.XPATH, '/html/body/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div[4]/div[2]/div/div/div'):
                contact_person += single_record.text.split("-")[0].strip()
                contact_person += ' '
            customer_details_data.contact_person = contact_person.rstrip(' ')
        except:
            pass
            

        try:
            customer_details_data.org_email= page_details.find_element(By.XPATH, '/html/body/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div[4]/div[2]/div/div/div').text.split("/")[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
            
        try:
            org_phone = ''
            for single_record in page_details.find_elements(By.XPATH, '/html/body/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div[4]/div[2]/div/div/div'):
                org_phone += single_record.text.split("-")[1].split("/")[0].strip()
                org_phone += ' '
            customer_details_data.org_phone = org_phone.rstrip(' ')
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        org_parent_id ="7030962"
        customer_details_data.org_parent_id = int(org_parent_id)
        
        
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)      
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
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://purcosa.co.za/tenders'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div/div/div/div/div/div/div/div/table/tbody/tr')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div/div/div/div/div/div/div/div/table/tbody/tr')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                    
            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

        if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
