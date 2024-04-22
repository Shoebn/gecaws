from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bh_etenderboard_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bh_etenderboard_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'bh_etenderboard_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BH'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'BHD'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    notice_data.document_type_description = "Tenders"	

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass   

    try:               
        customer_details_data = customer_details() 
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        customer_details_data.org_country = 'BH'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:  
        attachments_data = attachments()
        attachments_data.file_name = 'TENDER DOCUMENT'

        external_url_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(14) > a:nth-child(2)').get_attribute('onclick')
        url_no = external_url_no.split("('")[1].split("')")[0].strip()
        attachments_data.external_url = 'https://etendering.tenderboard.gov.bh/Tenders/template/TenderAdvertisement'+str(url_no)+'.pdf'
        time.sleep(5)
        
        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        except:
            pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_url = WebDriverWait(tender_html_element, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(14) > a:nth-child(1)')))
        page_main.execute_script("arguments[0].click();",notice_url)
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(7)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try: 
        publish_date = page_main.find_element(By.XPATH,'''(//*[contains(text(),"Tender Published Date")]//following::td[1])[1]''').text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S') 
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return   

    try:
        notice_data.local_description = page_main.find_element(By.XPATH,'''(//*[contains(text(),"Tender Description In English")]//following::td[1])[1]''').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH,'''(//*[contains(text(),"Contract Duration")]//following::td[1])[1]''').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH,'''(//*[contains(text(),"Tender Document Fee (BHD)")]//following::td[1])[1]''').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

    try: 
        document_opening_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Priced Bid Opening")]//following::td[1])[1]').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        document_purchase_start_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Tender Document Purchases Start Date")]//following::td[1])[1]').text
        document_purchase_start_time = re.findall('\d+-\d+-\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_end_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Tender Document Purchases End Date")]//following::td[1])[1]').text
        document_purchase_end_time = re.findall('\d+-\d+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

    try:
        earnest_money_deposit = page_main.find_element(By.XPATH, '(//*[contains(text(),"Tender Bond Value")]//following::td[1])[1]').text
        earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
        notice_data.earnest_money_deposit = earnest_money_deposit
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass

    try:
        deadline = page_main.find_element(By.XPATH, '(//*[contains(text(),"Bid Submission Closing")]//following::td[1])[1]').text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+',deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        cpvs_data = cpvs()
        cpv_code = page_main.find_element(By.XPATH,'''(//*[contains(text(),"Classification")]//following::td[1])[1]''').text
        cpvs_data.cpv_code = re.findall("\d{8}",cpv_code)[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpvs_data.cpv_code
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass

    try:
        notice_data.class_title_at_source = page_main.find_element(By.XPATH,'''(//*[contains(text(),"Classification")]//following::td[1])[1]''').text.split('-')[2].strip()
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.XPATH,'/html/body/form/div/div/div').get_attribute('outerHTML')
    except:
        pass

    try:
        notice_text_click = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'tr.even.gradeA > td:nth-child(2) > a')))
        page_main.execute_script("arguments[0].click();",notice_text_click)
        time.sleep(3)
    except:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div/div[4]/table'))).get_attribute('outerHTML')
    except:
        pass

    try:
        notice_text_close = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > form > div > div:nth-child(6) > table > tbody > tr > td > input')))
        page_main.execute_script("arguments[0].click();",notice_text_close)
        time.sleep(2)
    except:
        pass

    try:
        close = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > form > div > div > div > center > font > font > input')))
        page_main.execute_script("arguments[0].click();",close)
    except:
        pass
    page_main.switch_to.window(page_main.window_handles[0])
    
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#NewTndRecord > tbody > tr'))).text
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
    urls = ["https://etendering.tenderboard.gov.bh/Tenders/publicDash?viewFlag=NewTenders&CTRL_STRDIRECTION=LTR&encparam=viewFlag,CTRL_STRDIRECTION,randomno&hashval=78ca087819d1ecc2ccf72801acd105fc1538485253d7f8c5ff7fd61d0707a420#"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#NewTndRecord > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#NewTndRecord > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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