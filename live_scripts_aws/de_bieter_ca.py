from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_bieter_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
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
SCRIPT_NAME = "de_bieter_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_bieter_ca'
    
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 0   
    
    notice_data.notice_type = 7  

    details_page = tender_html_element.find_element(By.CSS_SELECTOR,'button')
    page_main.execute_script("arguments[0].click();",details_page)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app/supplier-portal-frame/div/div/mat-sidenav-container/mat-sidenav-content/project-award-details/div/div/div/mat-card/mat-card-content')))
    notice_data.notice_url = page_main.current_url

    
    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Veröffentlichungsdatum')]//following::div").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        page_main.back()
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="project-vertical-container"]/div')))
        return  

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3)").text
        notice_deadline = re.findall('\d+.\d+.\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.type_of_procedure_actual = page_main.find_element(By.XPATH, "//*[contains(text(),'Vergabeart')]//following::div").text
        type_of_procedure_actual_en = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_bieter_ca_procedure.csv",type_of_procedure_actual_en)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    notice_data.document_type_description = 'Award Announcements'
        
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '.mat-card.mat-focus-indicator').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
  
    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, "//*[contains(text(),'Projektnummer')]//following::div").text
    except:
        pass

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, "//*[contains(text(),'Titel')]//following::div").text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    
    try:              
        customer_details_data = customer_details()
                
        try:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '/html/body/app/supplier-portal-frame/div/div/mat-sidenav-container/mat-sidenav-content/project-award-details/div/div/div/mat-card/mat-card-content/div/div[3]/div[2]').text
        except:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, "//*[contains(text(),'Adresse')]//following::div").text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
   
    lot_details_data = lot_details()
    lot_details_data.lot_title = notice_data.notice_title
    notice_data.is_lot_default = True
    lot_details_data.lot_description = notice_data.local_title
    lot_details_data.lot_number = 1
    
    try:
        notice_contract_type = page_main.find_element(By.XPATH, "//*[contains(text(),'Leistungsart')]//following::div").text
        lot_details_data.contract_type = GoogleTranslator(source='auto', target='en').translate(notice_contract_type)
        if 'supplies' in lot_details_data.contract_type:
            lot_details_data.contract_type = 'Supply'
        elif 'Public Works' in lot_details_data.contract_type:
            lot_details_data.contract_type = 'Works'
        elif 'services' in lot_details_data.contract_type:
            lot_details_data.contract_type = 'Service'
        elif 'construction' in lot_details_data.contract_type:
            lot_details_data.contract_type = 'Works'
        else:
            pass
    except:
        pass
    
    try:
        notice_data.notice_contract_type = lot_details_data.contract_type
    except:
        pass
    try:
        award_details_data = award_details()
        award_details_data.bidder_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Firma')]//following::div").text
        award_details_data.award_date = notice_data.publish_date
        award_details_data.address = page_main.find_element(By.XPATH, "/html/body/app/supplier-portal-frame/div/div/mat-sidenav-container/mat-sidenav-content/project-award-details/div/div/div/mat-card/mat-card-content/div/div[22]/div[2]").text
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
    except Exception as e:
        logging.info("Exception in award_details: {}".format(type(e).__name__)) 
        pass
    lot_details_data.lot_details_cleanup()
    notice_data.lot_details.append(lot_details_data)
    
    page_main.back()
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="project-vertical-container"]/div')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ['https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/zuschlagsbekanntmachungen'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="project-vertical-container"]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))
                length = len(rows)
                for records in range(0, length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="662909-0"]/div/dashboard-widget/mat-card/dashboard-project-award-widget/mat-card-content/mat-paginator/div/div/div[2]/button[3]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(10)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="project-vertical-container"]/div'),page_check))
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
    
