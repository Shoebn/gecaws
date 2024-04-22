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
from gec_common.web_application_properties import *
script_name_log = "it_empulia"

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_empulia"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = "it_empulia"
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2    
    notice_data.notice_type = 4   
    notice_data.main_language = 'IT'
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
        
        notice_data.local_description = notice_data.local_title
        
        if 'Expression of interest' in  notice_data.notice_title:
            notice_data.notice_type = 7  
        else:
            notice_data.notice_type = 4   
        
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__))
        pass  
     
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip()) 
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'th > h1').text.split('(')[0]
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
       
    try:
        deadline_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        deadline_date = re.findall('\d+/\d+/\d{4} \d+:\d+',deadline_date)[0]
        notice_data.notice_deadline = datetime.strptime(deadline_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in deadline_date: {}".format(type(e).__name__))
        pass
     
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#template_doc > thead > tr > th > h1').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#template_doc').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH,"//*[contains(text(),'Incaricato')]//following::td").text
        except:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR," td:nth-child(3)").text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_description = page_details.find_element(By.XPATH,"//*[contains(text(),'Incaricato:')]//following::td").text
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        pass
        
    try:              
        tender_criteria_data = tender_criteria()
        try:
            tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH,"//*[contains(text(),'Criterio')]//following::td").text
        except Exception as e:
            logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
            pass

        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__))
        pass
    
    try:
        grossBudgetEuro = page_details.find_element(By.XPATH,"//*[contains(text(),'Importo Appalto:')]//following::td").text.split(' (')[0]
        grossBudgetEuro = re.sub("[^\d\.\,]", "",grossBudgetEuro)
        notice_data.grossBudgetEuro = float(grossBudgetEuro.replace('.','').replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in grossBudgetEuro: {}".format(type(e).__name__))
        pass
    
    try:           
        lot_details_data = lot_details()     
        
        lot_details_data.lot_number = 1
        
        try:
            lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(1) > td').text
        except:
            lot_details_data.lot_title = notice_data.notice_title 
        
        try:
            lot_details_data.lot_description = page_details.find_element(By.XPATH,"//*[contains(text(),'Descrizione breve')]//following::td").text
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        try:
            lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH,"//*[contains(text(),'Importo Appalto:')]//following::td").text
            lot_details_data.lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_details_data.lot_grossbudget_lc)
            lot_details_data.lot_grossbudget_lc = float(lot_details_data.lot_grossbudget_lc.replace('.','').replace(',','.').strip())
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass           

        try:
            contract_type = page_details.find_element(By.XPATH,"//*[contains(text(),'Tipo Appalto:')]//following::td").text
            
            if "Lavori pubblici" in contract_type:       
                lot_details_data.contract_type="Works"
            elif "Servizi" in contract_type:     
                lot_details_data.contract_type="Service"    
            elif "Forniture" in contract_type:
                lot_details_data.contract_type="Supply"     
            else:
                pass
    
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)          
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass
    
    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Scarica Allegati'
        number = notice_data.notice_url.split('&bando=')[1].split('&')[0]
        external_url = page_details.find_element(By.CSS_SELECTOR, 'input#DownloadAllegati').get_attribute('onclick').split("'")[1].split("'")[0]
        attachments_data.external_url = external_url+number
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Bandi%20di%20gara%20new.aspx'] 
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_m_g_e1473ed7_3e49_4d7a_8380_ca0aaa3c0eda_dgList"]/tbody/tr[3]'))).text
            for tender_html_element in WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_m_g_e1473ed7_3e49_4d7a_8380_ca0aaa3c0eda_dgList"]/tbody/tr')))[2:-1]:
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.LINK_TEXT,str(page_no)))).click()   
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_m_g_e1473ed7_3e49_4d7a_8380_ca0aaa3c0eda_dgList"]/tbody/tr[3]'),page_check))   
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
#     page_main.quit() 
#     page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
