from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_aaiaero_spn"
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
import gec_common.Doc_Download_ingate as Doc_Download
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_aaiaero_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'INR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    notice_data.script_name = "in_aaiaero_spn"
    
    try:
        clk = tender_html_element.find_element(By.CSS_SELECTOR, "span > div > div.col-md-12.tender-name").click()
        time.sleep(5)
    except:
        pass
    
    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, ' div.col-md-4.tender_type.col-md-4').text.split("Tender Type:")[1].strip()
        if 'Domestic' in procurement_method:
            notice_data.procurement_method = 0
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12.tender-name > div.col-md-10').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    notice_data.notice_url = url
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_no = tender_html_element.text.split("E-Bid No : ")[1].split("Status :")[0].split("Download")[0].split("/n")[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12.tednder_description p').text
        if len(local_description) <=1:
            pass
        else:
            notice_data.local_description = local_description
            
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " div.general-info > div > div > div:nth-child(2)").text
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        cpv_at_source = ''
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "div.general-info > div > div > div:nth-child(3)").text.split("Department :")[1].strip()
        category = notice_data.category.lower()
        cpv_codes = fn.CPV_mapping("assets/in_aaiaero_spn_cpv.csv",category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
            cpv_at_source += cpv_code
            cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "Airports Authority Of India"
        
        org_parent_id ="1483743"
        customer_details_data.org_parent_id = int(org_parent_id)
        

        try:
            customer_details_data.org_city  = tender_html_element.find_element(By.CSS_SELECTOR, ' div.general-info > div > div > div:nth-child(1)').text.split("Region / Airport :")[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try: 
        clk = tender_html_element.find_element(By.CSS_SELECTOR, " div:nth-child(3) > a > div").click()
        time.sleep(5)
    except:
        pass

    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, "tr:nth-child(6) > td:nth-child(2)").text
        document_purchase_start_time = re.findall('\d+-\w+-\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, " tr:nth-child(8) > td:nth-child(2)").text
        document_purchase_end_time = re.findall('\d+-\w+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr:nth-child(8) > td:nth-child(2)").text
        notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:              
        attachments_data = attachments()

        attachments_data.file_name = "Download"
        
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > a').get_attribute('href')
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    try:
        clk = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > a > div > i").click()
        time.sleep(5)
    except:
        pass
    
    try:              
        attachments_data = attachments()
        #tr:nth-child(2) > td:nth-child(3)

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, ' tr:nth-child(2) > td:nth-child(4) > a').text
        
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, ' tr:nth-child(2) > td:nth-child(4) > a').get_attribute('href')
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.aai.aero/en/tender/tender-search?field_region_tid=All&field_airport_tid=All&term_node_tid_depth=All&field_tender_status_value=All&field_tender_last_sale_date_value%5Bvalue%5D%5Bdate%5D=&combine='] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        value= "0"
        select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'select#edit-field-tender-status-value.form-select'))
        select_fr.select_by_value(value)
        
        try:
            clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' #edit-submit-tender'))).click()
        except:
            pass

        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div/div/div/div[2]/section/div[1]/div/div/div/div[2]/div/ul/li/div/span/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div/div[2]/section/div[1]/div/div/div/div[2]/div/ul/li/div/span/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div/div[2]/section/div[1]/div/div/div/div[2]/div/ul/li/div/span/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[4]/div/div/div/div[2]/section/div[1]/div/div/div/div[2]/div/ul/li/div/span/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
        except:
            logging.info('No new record')
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
