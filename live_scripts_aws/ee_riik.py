from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ee_riik"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ee_riik"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ee_riik'
    notice_data.main_language = 'ET'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'EE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4

    notice_data.currency = 'EUR'

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(1) > span:nth-child(2)').text  
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(3) > rhr-domain-value > span').text  
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(4) > span:nth-child(2)').text  
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > ul > li:nth-child(2) > span:nth-child(2)").text  
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li.ng-scope > span:nth-child(2)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.XPATH, '//*[@id="ng-app"]/body/div[2]/rhr-search/rhr-main-content/main/ng-transclude/div/div/rhr-search-result/div/div/div[1]/h2').text  
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'rhr-search-result-row > h3 > a').get_attribute("href")        
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > rhr-form > form').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'rhr-search-result-row > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Hanke lühikirjeldus:')]//following::p[1]").text 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:   
        notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Hanke liik:')]//following::span[2]").text  
        if 'Teenused' in notice_contract_type:
            notice_data.notice_contract_type  ='Servics'
        elif 'Asjad' in notice_contract_type:
            notice_data.notice_contract_type  = 'supply'
        elif 'Ehitustööd' in notice_contract_type:
            notice_data.notice_contract_type = 'work'
        else:
            pass

    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:       
        est_amount = page_details.find_element(By.CSS_SELECTOR, "ng-transclude > rhr-input-currency > div > p").text  
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace(',','.').strip()
        notice_data.est_amount =float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Kestus kuudes')]//following::div[1]").text  
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    try:              
        customer_details_data = customer_details()
        try:
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > ul > li:nth-child(2) > span:nth-child(2)').text   
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Vastutav isik:')]//following::p[1]").text   
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'EE'
        customer_details_data.org_language = 'ET'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, "td:nth-child(1)"):
            cpvs_data = cpvs()

            try:
                cpvs_data.cpv_code = single_record.find_element(By.CSS_SELECTOR, "strong").text.split('-')[0]     
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        Evaluation_criteria_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@translate,'procurement.menu.item.evaluation')]")))  
        page_details.execute_script("arguments[0].click();",Evaluation_criteria_click)
        logging.info("Evaluation_criteria_click")
        time.sleep(5)
    except:
        pass

    try:              
        for single_record in WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr'))):
            tender_criteria_data = tender_criteria() 
            
            try:
                tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text  
            except :
                try:
                    tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'a.row-title.expandable.ng-scope').text  
                except Exception as e:
                    logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                    pass
            try:
                tender_criteria_weight = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3) > span').text  
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
            except Exception as e:  
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

        
    try:
        attachment_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@translate,'procurement.menu.item.documents')]")))  
        page_details.execute_script("arguments[0].click();",attachment_click)
        time.sleep(2)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url= (str(file_dwn[0]))
    except:   
        pass
    
    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Download valid procurement documents'

        external_url = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'span > rhr-button.ng-scope.ng-isolate-scope > button')))
        page_details.execute_script("arguments[0].click();",external_url)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url= (str(file_dwn[0]))
        attachments_data.file_type = '.zip'

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass  

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')

arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://riigihanked.riik.ee/rhr-web/#/search"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
    
        Avaleht_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'header > nav.navbar.navbar-subnav > div > div > ul > li:nth-child(1) > a')))
        page_main.execute_script("arguments[0].click();",Avaleht_click)
        logging.info("Avaleht_click")
        
        recent_tenders_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div > p:nth-child(2) > a:nth-child(2)')))
        page_main.execute_script("arguments[0].click();",recent_tenders_click)
        logging.info("recent_tenders_click")
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/rhr-search/rhr-main-content/main/ng-transclude/div/div/rhr-search-result/div/div/ol/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/rhr-search/rhr-main-content/main/ng-transclude/div/div/rhr-search-result/div/div/ol/li')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    
