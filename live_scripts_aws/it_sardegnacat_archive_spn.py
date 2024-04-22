#NOTE- "if page get expire overright the url again" .... after clicking on login page click on "Bandi di gara"

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_sardegnacat_archive_spn"
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
import gec_common.Doc_Download_VPN

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "it_sardegnacat_archive_spn"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'it_sardegnacat_archive_spn'
   
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
   
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -if following word is encountered "Expression of interest" then take as "5" use following selector to check EOI "td:nth-child(2)"
    
    
    # Onsite Field -Descrizione Bando di Gara
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    # Onsite Field -Scadenza Manifestazione d'Interesse
    # Onsite Comment -just take data for published date from Data ultima modifica
    
    # Onsite Field -Descrizione Bando di Gara
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_sardegnacat_spn_procedure.csv",type_of_procedure_actual)
        if "Expression of interest" in type_of_procedure_actual:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia Prestazione
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if 'Servizi' in notice_data.contract_type_actual or 'Lavori' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif "Forniture" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scadenza Manifestazione d'Interesse
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
        
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
        
    try:
        notice_url_click = WebDriverWait(tender_html_element,150).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'td:nth-child(4)>a')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        time.sleep(10)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        pass
    
    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr"
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#opportunityDetailFEBean > div').get_attribute("outerHTML")                     
        time.sleep(2)
    except:
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
        
        
     # Onsite Field -Codice Bando di Gara
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, "//*[contains(text(),'Codice Bando di Gara')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Descrizione')]//following::div[9]").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descrizione
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Descrizione Bando di Gara
    # Onsite Comment -None

        customer_details_data.org_name = org_name

    # Onsite Field -Email
    # Onsite Comment -None

        try:
            org_email = page_main.find_element(By.XPATH, "//*[contains(text(),'Email')]//following::div[1]").text
            customer_details_data.org_email =re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contatto
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, "//*[contains(text(),'Contatto')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:                                                                      
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Data ultima modifica')]//following::td[5]").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    try:              
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > div:nth-child(9) > div > ul > li > table > tbody > tr')[1:]:        
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            try:
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            except:
                pass
        # Onsite Field -Codice
        # Onsite Comment -take data from "Lotti Pubblicati" only

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

        # Onsite Field -Titolo
        # Onsite Comment -take data from "Lotti Pubblicati" only

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

        # Onsite Field -Descrizione
        # Onsite Comment -click on Colonna Azione" for details use following selector "#opportunityDetailFEBean  button > span '
        
            click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6) button').click()
            page_main.switch_to.window(page_main.window_handles[1])
            time.sleep(3)

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Descrizione')]//following::td[1]").text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except:
                pass
            page_main.switch_to.window(page_main.window_handles[0])

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Colonna Azione" for details use following selector "#opportunityDetailFEBean button > span "

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > div:nth-child(9) > div > ul > li > table > tbody > tr')[1:]:
            attachments_data = attachments()

            attachments_data.file_name = "Download PDF" 

            click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6) button').click()
            page_main.switch_to.window(page_main.window_handles[1])
            time.sleep(3)
            external_url = page_main.find_element(By.CSS_SELECTOR, 'input[type=button]:nth-child(4)')
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            page_main.switch_to.window(page_main.window_handles[0])
            attachments_data.file_type = "pdf"
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
#     # Onsite Field -CIG/Smart CIG
#     # Onsite Comment -click on "Colonna Azione" for details use following selector "#opportunityDetailFEBean button > span "
    
    try:
        if notice_data.publish_date is None:
            click = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(6) button').click()
            page_main.switch_to.window(page_main.window_handles[1])
            time.sleep(5)
            try:                                                                      
                publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Pubblicazione')]//following::td[1]").text
                publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except:
                pass
            page_main.switch_to.window(page_main.window_handles[0])
            time.sleep(3)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
# # Onsite Field -None
# # Onsite Comment -Allegati dell'Avviso
#                                                                                 
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, ' div:nth-child(13) > div > ul > li > table > tbody > tr')[1:]:
            attachments_data = attachments()

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')

            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('title')
            file_name = file_name.split("Scarica il file:")[1].split("'")[1].split("'")[0].strip()
            
            if ".pdf" in file_name:
                attachments_data.file_name = file_name.replace(".pdf","").strip()
            elif ".zip" in file_name:
                attachments_data.file_name = file_name.replace(".zip","").strip()
            elif ".docx" in file_name:
                attachments_data.file_name = file_name.replace(".docx","").strip()
            else:
                attachments_data.file_name = file_name.replace(".pdf","").strip()
            

            try:
                file_type = file_name
                if ".pdf" in file_type:
                    attachments_data.file_type = 'pdf'
                elif ".zip" in file_type:
                    attachments_data.file_type = 'zip'
                elif ".docx" in file_type:
                    attachments_data.file_type = 'docx'
                else:
                    attachments_data.file_type = 'pdf'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass


    #         # Onsite Field -Nome
    #         # Onsite Comment -take data from "Allegati dell'Avviso" only ---- if description is present grab description...

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) ').text.split("(")[1].split(")")[0].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
#     page_main.execute_script("window.history.go(-1)")
    page_main.find_element(By.XPATH,'//*[@id="titleToolbar"]/div[1]/div[1]/button').click()
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized','--disable-notifications']
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.sardegnacat.it/esop/guest/go/public/opportunity/current"]
    for url in urls:
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)

        procedure_non_in_corso = page_main.find_element(By.XPATH,'//*[@id="tabMenu3Level"]/div[2]/div/a').click()
        time.sleep(2)
        #page range 0 = website page 1
        #please pass here page range accordingly
        for page_no in range(0):
            logging.info(page_no)
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr[1]'))).text

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@title="Avanti"]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                time.sleep(3)
                page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr[1]'))).text
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr[1]'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                pass
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))[records]
            logging.info(tender_html_element.text)
            extract_and_save_notice(tender_html_element)
            
            if notice_count == 50:
                output_json_file.copyFinalJSONToServer(output_json_folder)
                output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                notice_count = 0
                
            if notice_count >= MAX_NOTICES:
                break
                    
            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))

finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
