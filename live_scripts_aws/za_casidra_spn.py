from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_casidra_spn"
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
SCRIPT_NAME = "za_casidra_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'ZAR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.script_name = "za_casidra_spn"
    
    notice_data.procurement_method = 2
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h3.df-cpt-title').text
        if "RE-ADVERTISEMENT" in notice_data.local_title:
            notice_data.notice_type = 7
        else:
            notice_data.notice_type = 4
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass  
    
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'h3.df-cpt-title').text            
        try:
            notice_data.notice_no = re.findall('[A-Za-z]+ \d+',notice_no)[0]
        except:
            notice_data.notice_no = re.search('[A-Za-z\d]+',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tender_button_div.et_pb_button_module_wrapper.et_pb_button_alignment_left.et_pb_module > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Basic Information
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
        
    try:
        publish_date = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Post Date:")])//following::div[1]''').text
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Closing Date:")])//following::div[1]''').text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "Casidra"
        
        customer_details_data.org_address = "P O Box 660,Southern Paarl,7624,22 Louws Avenue, Southern Paarl, WP 7646, South Africa"
       
        customer_details_data.org_phone = "+27(0)21 863-5000,+27(0)21 863-1055"
        
        org_parent_id ="7525404"
        customer_details_data.org_parent_id = int(org_parent_id)
        
        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '(//*[contains(text(),"Location:")])//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Contact Person:")])//following::div[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Contact Email:")])//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        local_description = page_details.find_element(By.CSS_SELECTOR, '#main-content > div > div').text.split("scope of works will include.")[1].split("SUBMISSION OF DOCUMENTS")[0].strip()
        notice_data.local_description = local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description[:4500]) 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__)) 
        pass
    
    try:
        attach = page_details.find_element(By.CSS_SELECTOR, "#docsbutton > a").click()
        time.sleep(5)
    except:
        pass
    try:
        name_box = page_details.find_element(By.ID,'input_2_7_3')
        name_box.send_keys('sadf')
        time.sleep(2)
    except:
        pass
    
    try:
        surname_box = page_details.find_element(By.ID,'input_2_7_6')
        surname_box.send_keys('sadf')
        time.sleep(2)
    except:
        pass
    
    try:
        email_box = page_details.find_element(By.CSS_SELECTOR,'#input_2_3')
        email_box.send_keys('sadf@gmail.com')
        time.sleep(2)
    except:
        pass
    
    try:
        submit = page_details.find_element(By.CSS_SELECTOR, "#gform_submit_button_2").click()
        time.sleep(5)
    except:
        pass
    
    try:  
        attachments_data = attachments()

        attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#hidden_downloads > ul > li').text

        attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#hidden_downloads > ul > li > a').get_attribute('href')
            
            
        attachments_data.file_type = "pdf"
        

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
        
 
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://tenders.casidra.co.za/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
       
        for page_no in range(2,6):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/article/div/div/div/div/div[3]/div/div/div/div/div/div/div[1]/article'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div[2]/div/article/div/div/div/div/div[3]/div/div/div/div/div/div/div[1]/article')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div[2]/div/article/div/div/div/div/div[3]/div/div/div/div/div/div/div[1]/article')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div/div[2]/div/article/div/div/div/div/div[3]/div/div/div/div/div/div/div[1]/article'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
