
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_eappaltifvg_spn"
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
import gec_common.Doc_Download_VPN as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_eappaltifvg_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'it_eappaltifvg_spn'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    

    notice_data.procurement_method = 2
    

    notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    if 'Manifestazione di Interesse' in notice_type:
        notice_data.notice_type  = 5
    else:
        notice_data.notice_type = 4
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M') + ':00' 
        logging.info('notice_deadline',notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Vendita' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Locazione'in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
        
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    notice_data.notice_url = url
    
    notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)>a').get_attribute("onclick")
    notice_url = notice_url.split("goToDetail('")[1].split("',")[0]
    notice_url = 'https://eappalti.regione.fvg.it/esop/toolkit/opportunity/current/'+str(notice_url)+'/detail.si'
    logging.info(notice_url)

    fn.load_page(page_main, notice_url, 50)
    time.sleep(4)
    
    
    try:
        publish_date = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#opportunityDetailFEBean > div > div:nth-child(13) > div > ul > li > table > tbody > tr:nth-child(3) > td:nth-child(5)'))).text
        publish_date = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date= datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M') + ':00'  
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#opportunityDetailFEBean > div').get_attribute("outerHTML") 
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, "//*[contains(text(),'Codice Cartella di Gara')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Descrizione')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_summary_english =  GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()


        try:
            customer_details_data.org_name = org_name
        except:
            customer_details_data.org_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Stazione Appaltante')]//following::div[1]").text


        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, "//*[contains(text(),'Email')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

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
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > div:nth-child(9) > div > ul > li > table > tbody > tr')[1:]:
            attachments_data = attachments()

            try:
                attachments_data.file_name = 'Tender Document'
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            popup_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)>button')
            page_main.execute_script("arguments[0].click();",popup_url)
            time.sleep(5)
            page_main.switch_to.window(page_main.window_handles[1])  
            logging.info('went inside pop up')
            WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="cntDetail"]'))).text

            ########################### data taken from the pdf pop up ##########################
            try:
                lot_description = page_main.find_element(By.XPATH,"//*[contains(text(),'Descrizione')]//following::td[1]").text
            except:
                pass

            if notice_data.publish_date is None or notice_data.publish_date =='':
                try:
                    publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Pubblicazione')]//following::td[1]").text
                    publish_date = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}:\d{2}',publish_date)[0]
                    notice_data.publish_date= datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S') 
                    logging.info(notice_data.publish_date)
                except Exception as e:
                    logging.info("Exception in publish_date: {}".format(type(e).__name__))
                    pass

            ################################################################

            external_url = page_main.find_element(By.CSS_SELECTOR,'#cntDetail > input[type=button]:nth-child(4)')
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            logging.info('2nd type attachment %s', attachments_data.external_url)

            time.sleep(2)

            try:
                attachments_data.file_type = 'pdf'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

            page_main.close()                                         
            page_main.switch_to.window(page_main.window_handles[0])

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    try:
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > div:nth-child(9) > div > ul > li > table > tbody > tr')[1:]:
            lot_details_data = lot_details()


            try:
                lot_details_data.lot_actual_number = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_number = lot_number

            try:
                lot_details_data.lot_title = page_main.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_description = lot_description
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
                    
            try:                             
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual                                
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
                pass 

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1 
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass


    try:
        notice_data.related_tender_id = page_main.find_element(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > div:nth-child(6) > div > ul > li:nth-child(1) > div.form_answer').text.split('CIG: ')[1].split(' – ')[0]
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass


    try:              
        for single_record in page_main.find_elements(By.XPATH, '//*[@id="opportunityDetailFEBean"]/div/div[8]/div/ul/li/table/tbody/tr | //*[@id="opportunityDetailFEBean"]/div/div[10]/div/ul/li/table/tbody/tr')[1:]:
            attachments_data = attachments()


            try:
                file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)>a').get_attribute('title').replace('Scarica il file:','')
                parts = file_name.split('.')
                name = '.'.join(parts[:-1])
                if '.pdf' in name:
                    name = name.replace('.pdf','')
                attachments_data.file_name  = name
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)>a')
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(2)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])


            try:
                if 'pdf' in file_name:
                    attachments_data.file_type = 'pdf'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass


            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text.split('(')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
  
    page_main.execute_script("window.history.go(-1)")
    time.sleep(4)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr[1]'))).text

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
page_main =  Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://eappalti.regione.fvg.it/web/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        Bandi_e_avvisi = page_main.find_element(By.CSS_SELECTOR,'#homepage > div.container > div > div:nth-child(2) > div > ul:nth-child(3) > li > a').click()
        time.sleep(1)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
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
    
