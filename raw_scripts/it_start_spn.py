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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_start_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.procurement_method = 2
    
    notice_data.script_name = 'it_start_spn'
    
    notice_data.main_language = 'IT'
        
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
        
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4
    
    notice_data.document_type_description = 'Bandi e avvisi'
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject a').text
        notice_data.notice_title=GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)  
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title".format(type(e).__name__))
        pass
    
    try:
        amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td.amount').text
        amount = re.sub("[^\d\.\,]", "", amount)
        est_amount = float(amount.replace('.','').replace(',','.').strip())   
        notice_data.grossbudgetlc = est_amount
    except Exception as e:
        logging.info("grossbudgetlc".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.contractType').text
        if 'Servizi' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("notice_contract_type".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.publishedAt").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("publish_date".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > span.protocolId').text
    except Exception as e:
        logging.info("Exception in notice_no".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english  = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text
        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        notice_data.notice_url = url
        logging.info("Exception in notice_url".format(type(e).__name__))

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'ng-component').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text".format(type(e).__name__))
        pass
    

    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "div.label.pad-top-20px > ul > li:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')     
    except Exception as e:
        logging.info("Exception in notice_deadline".format(type(e).__name__))
        pass
    
    try:
        cookie_click = WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.XPATH,'/html/body/tendering-app/pleiade-footer2/div[3]/div/nav/div/button')))
        page_details.execute_script("arguments[0].click();",cookie_click)
    except:
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.box-content.pad-20px.collapsible-content > div > div > div:nth-child(3) > div.pad-left-20px'):  
            attachments_data = attachments()
            attachments_data.file_type = 'pdf'
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'h3').text 
            external_url = single_record.find_element(By.CSS_SELECTOR, 'div > a').click() 
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'div > span:nth-child(4)').text.split(':')[1].strip()  
            except Exception as e:
                logging.info("Exception in file_size".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments".format(type(e).__name__))
        pass
    
    
    try:    
        clk1 = WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.LINK_TEXT,'ELENCO LOTTI')))
        page_details.execute_script("arguments[0].click();",clk1)
        
        time.sleep(5)
        
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        
        try:
            lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.border-right.width-20').text
        except:
            lot_details_data.lot_title = notice_data.notice_title

        try:
            lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'lot-item > div:nth-child(4)').text
            lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_lc)
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
        except Exception as e:
            logging.info("Exception in lot_grossbudgetlc: {}".format(type(e).__name__))
            pass

        try:
            lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'lot-item > div:nth-child(5)').text  
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
            
            			
        # Onsite Field -None
        # Onsite Comment -in "Elenco lotti" click on 2 tab "CONFIGURAZIONE OFFERTA" to get data 
            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.form-container > div:nth-child(3)'):
                    lot_criteria_data = lot_criteria()
		
            # Onsite Field -AWARD CRITERIA
            # Onsite Comment -None

                    try:
                        lot_criteria_data.lot_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.form-container > div:nth-child(3) > div').text
                    except Exception as e:
                        logging.info("Exception in lot_criteria_title: {}".format(type(e).__name__))
                        pass
            # Onsite Field -AWARD CRITERIA
            # Onsite Comment -take only numeric value 

                    try:
                        lot_criteria_data.lot_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.form-container > div:nth-child(3) > div').text
                    except Exception as e:
                        logging.info("Exception in lot_criteria_weight: {}".format(type(e).__name__))
                        pass
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass


        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details".format(type(e).__name__))
        pass
    
    try:
        tender_criteria_data = tender_criteria()
        tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'lot-item > div:nth-child(5)').text  
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria".format(type(e).__name__))
        pass


    try:
        clk2 = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,'CLASSIFICAZIONE')))
        page_details.execute_script("arguments[0].click();",clk2)
        time.sleep(5)
    except:
        pass
    
    try:
        cpvs_data = cpvs()
        cpv_text  = page_details.find_element(By.CSS_SELECTOR, 'classification-first-level > div > div > div > div:nth-child(2) > div > span').text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data.cpv_code = cpv_regex.findall(cpv_text)[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs".format(type(e).__name__))
        pass

    try:
        clk3 =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Dettagli')))
        page_details.execute_script("arguments[0].click();",clk3)     
        time.sleep(5)
    except:
        pass
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Valore stimato della procedura:')]//following::span[1]").text.split('€')[1].strip()
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)
        notice_data.grossbudgetlc = float(grossbudgetlc.replace('.','').replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Scelta del contraente: ')]//following::span[1]").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_start_spn_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
                                                  
    try:
        earnest_money_deposit  = page_details.find_element(By.CSS_SELECTOR, 'div.collapsible-content > div > div > ul > li:nth-child(9) > span.value').text 
        if '€' in earnest_money_deposit:
            earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
            earnest_money_deposit = earnest_money_deposit.replace('.','').replace(',','.').strip()
            notice_data.earnest_money_deposit = earnest_money_deposit
        else:
            pass
    except Exception as e:
        logging.info("Exception in earnest_money_deposit".format(type(e).__name__))
        pass
    
        # Onsite Field -Importo (al netto dell’IVA):
    # Onsite Comment -None

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo (al netto dell’IVA):")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -Importo (al netto dell’IVA):
    # Onsite Comment -None

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo (al netto dell’IVA):")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
        
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    

    urls = ['https://start.toscana.it/index/index/hideAnnouncements/true']    
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#Contenuto > table > tbody > tr:nth-child(1)'))).text   
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#Contenuto > table > tbody > tr')))      
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#Contenuto > table > tbody > tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#Contenuto > table > tbody > tr:nth-child(1)'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: ", str(type(e)))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()  
    output_json_file.copyFinalJSONToServer(output_json_folder)
