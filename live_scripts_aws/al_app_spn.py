from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "al_app_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
button_no = 1
SCRIPT_NAME = "al_app_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global button_no
    notice_data = tender()
    
    notice_data.script_name = 'al_app_spn'

    notice_data.main_language = 'SQ'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AL'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'LEK'

    notice_data.notice_type = '4'

    notice_data.procurement_method = 2
    
    notice_data.notice_url = url

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-10.col-md-10.col-sm-10.col-xs-12').text.split(':')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Number:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li:nth-child(7) > span').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Open Date
    # Onsite Comment -None

    try:
        p_date = tender_html_element.find_element(By.CSS_SELECTOR, "li:nth-child(3) > span").text
        publ_date = re.findall('\d+-\d+-\d{4}',p_date)[0]
        p_time = re.findall('\d+:\d+',p_date)[0]
        publish_date = str(publ_date) + ' ' + str(p_time)
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Close Date:
    # Onsite Comment -None

    try:
        deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(5) li:nth-child(5)").text
        deadline_date = re.findall('\d+-\d+-\d{4}',deadline)[0]
        d_time = re.findall('\d+:\d+',deadline)[0]
        notice_deadline = str(deadline_date) + ' ' + str(d_time)
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
       
    # Onsite Field -Limit Fund
    # Onsite Comment -it is not present in each tender so just take from those tender where it is found ----- split from "Limit Fund" till Has Lots"

    try:
        es_amount = tender_html_element.text
        est_amount = es_amount.split('Limit Fund:')[1].split('Lekë')[0].strip()
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Limit Fund
    # Onsite Comment -it is not present in each tender so just take from those tender where it is found ----- split from "Limit Fund" till Has Lots"

    try:
        budgetlc = tender_html_element.text
        grosslc = budgetlc.split('Limit Fund:')[1].split('Lekë')[0].strip()
        grossbudgetlc = re.sub("[^\d\.\,]","",grosslc)
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Is Canceled:        pass "true" if "yes" , pass "false" if "no"
    # Onsite Comment -it is not present in each tender so just take from those tender where it is found ----- split from "Is Canceled:" till "Suspended"

    try:
        tender_is_canceled = tender_html_element.text
        if 'Is Canceled: Yes' in tender_is_canceled:
            notice_data.tender_is_canceled = True
        else:
            notice_data.tender_is_canceled = False
    except Exception as e:
        logging.info("Exception in tender_is_canceled: {}".format(type(e).__name__))
        pass
    # Onsite Field -Contract Type :
    # Onsite Comment -None  mainData_CN-10379-12012023 myModal_CN-10379-12012023
    try:
        notice_data_id = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-2.col-md-2 > div > div > div > div > a').get_attribute('href').split('#')[1]
        n_id = notice_data_id.replace('myModal','mainData').strip()
    except:
        pass
    
    try:
        notice_data_text = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-2.col-md-2 > div > div > div > div > a').click()
        time.sleep(3)
    except:
        pass
        

    try:
        notice_data.notice_contract_type = page_main.find_element(By.CSS_SELECTOR, '#'+str(n_id)+'> ul > li:nth-child(4) > div > div.col-lg-8.col-md-8.col-sm-12.col-xs-12 > small').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Type :
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_main.find_element(By.CSS_SELECTOR, '#'+str(n_id)+'> ul > li:nth-child(4) > div > div.col-lg-8.col-md-8.col-sm-12.col-xs-12 > small').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedures
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = page_main.find_element(By.CSS_SELECTOR, '#'+str(n_id)+'> ul > li:nth-child(3) > div > div.col-lg-8.col-md-8.col-sm-12.col-xs-12 > small').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/al_app_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -as it is page main the selector is selecting all notice text
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#'+str(n_id)+'> ul').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Contracting Authority:
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(1) > span').text.split(':')[1].strip()

        customer_details_data.org_country = 'AL'
        customer_details_data.org_language = 'SQ'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
 

    # Onsite Field -
# Onsite Comment -None

    try:              
        cpvs_data = cpvs()
    # Onsite Field -
    # Onsite Comment -
        try:
            cpv_code = page_main.find_element(By.CSS_SELECTOR, '#'+str(n_id)+'> ul > li:nth-child(10) > div > div.col-lg-8.col-md-8.col-sm-12.col-xs-12 > small').text
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
# Onsite Field -Tender Documents
# Onsite Comment -click on More info >>>  Tender Documents 
 
    try:  
        doc_id = n_id.split('CN')[1].strip()
        attachment_click = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.LINK_TEXT,'Tender Documents')))
        page_main.execute_script("arguments[0].click();",attachment_click) 
        time.sleep(3)
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#tenderdocuments_CN'+str(doc_id)+' div.col-lg-10.col-md-10.col-sm-9.col-xs-8 > p > a'):
            attachments_data = attachments()
        # Onsite Field -Tender Documents
        # Onsite Comment -just take tender document title
            try:
                attachments_data.file_name = single_record.text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        # Onsite Field -Tender Documents
        # Onsite Comment -just take external url

            attachments_data.external_url = single_record.get_attribute('href')

        # Onsite Field -Tender Documents
        # Onsite Comment -just take external url

            try:
                attachments_data.file_type = single_record.text.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        close_button = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@id="modal-form"]/div/div[3]/button)['+str(button_no)+']')))
        page_main.execute_script("arguments[0].click();",close_button)
        time.sleep(5)
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/div[3]/div'))).text
    except:
        pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    button_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://app.gov.al/contract-notice"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/div[3]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/div[3]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/div[3]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div[2]/div[3]/div'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
