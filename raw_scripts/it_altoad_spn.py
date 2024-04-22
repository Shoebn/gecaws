from gec_common.gecclass import *
import logging
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
import functions as fn
from functions import ET
import gec_common.Doc_Download
from webdriver_manager.chrome import ChromeDriverManager

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_altoad_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_altoad_spn'
    
    notice_data.main_language = 'IT'
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr  td.subject').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.publishedAt").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td.amount').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(notice_data.est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'span.protocolId').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,180)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text = page_details.find_element(By.CSS_SELECTOR, ' ng-component > div.no-errors > div > form').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr td.subject').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'span.process-type').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "li:nth-child(2) > span.stats-value").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'

        try:
            org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass

    try:               
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'attachments-section > div:nth-child(1) > div.box-content.pad-20px.collapsible-content > div > div'):
            attachments_data = attachments()
            try:
                file_type = single_record.find_element(By.CSS_SELECTOR,'div.pad-left-20px > div > a').text
                if 'pdf' in file_type:
                    attachments_data.file_type = 'pdf'
                elif 'PDF' in file_type:
                    attachments_data.file_type = 'pdf'
                elif 'zip' in file_type:
                    attachments_data.file_type = 'zip'
                elif 'ZIP' in file_type:
                    attachments_data.file_type = 'zip'
                elif 'DOCX' in file_type:
                    attachments_data.file_type = 'DOCX'
                elif 'docx' in file_type:
                    attachments_data.file_type = 'docx'
                elif 'XLS' in file_type:
                    attachments_data.file_type = 'XLS'
                elif 'xlsx' in file_type:
                    attachments_data.file_type = 'xlsx'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.pad-left-20px > h3').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.pad-left-20px > div > a')
            page_details.execute_script("arguments[0].click();",attachments_data.external_url)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            try:
                attachments_data.file_size = single_record.text.split('Dimensione:')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.contractType').text
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Lavori pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
                          
    try: 
        page_details1_url = page_details.find_element(By.CSS_SELECTOR, 'div.form-builder-header ul > li:nth-child(2) > a').get_attribute("href")
        fn.load_page(page_details1,page_details1_url,80)
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'classification-first-level > div > div > div > div:nth-child(2) > div'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('-')[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass
    
    try: 
        Elenco_lotti = page_details.find_element(By.CSS_SELECTOR, 'div.form-builder-header ul > li:nth-child(4) > a').text
        if 'ELENCO LOTTI' in Elenco_lotti:
            page_details2_url = page_details.find_element(By.CSS_SELECTOR, 'div.form-builder-header ul > li:nth-child(4) > a').get_attribute("href")
            fn.load_page(page_details2,page_details2_url,80)
            lot_number = 1
            for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'li.lot-item-container'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_grossbudget = single_record.find_element(By.CSS_SELECTOR, 'lot-item > div:nth-child(4) > div.pad-btm-10px').text
                    lot_grossbudget = re.sub("[^\d\.\,]", "", lot_grossbudget)
                    lot_details_data.lot_grossbudget = float(lot_grossbudget.replace('.','').replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                    pass

                try:
                    lot_title = single_record.find_element(By.CSS_SELECTOR, 'lot-item div.lot-item-name a').text
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                except:
                    lot_details_data.lot_title = notice_data.notice_title

                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.pad-btm-10px').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass
         
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
page_details = Doc_Download.page_details
page_details1 = fn.init_chrome_driver(arguments)
page_details2 = fn.init_chrome_driver(arguments)


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.bandi-altoadige.it/index/index/page/1'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Contenuto"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li:nth-child(12) > a')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    page_details1.quit()
    page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
