from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_ausschreib"
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
SCRIPT_NAME = "de_ausschreib"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_ausschreib'
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.tenderPublication").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td.tenderType").text
        type_of_procedure_en = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_ausschreib_procedure.csv",type_of_procedure_en)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.tenderDeadline").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender').text.split('(')[1].split(')')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    details = tender_html_element
    page_main.execute_script("arguments[0].click();",details)
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.ID,'printarea')))
        notice_data.notice_url = page_main.current_url
    except:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    
    try:
        dispatch_date = page_main.find_element(By.XPATH, '//*[contains(text(),"VI.5) Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
 
    try:
        notice_data.notice_contract_type = page_main.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
  
    try:
        notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td[5]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    

    try:              
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_main.find_element(By.CSS_SELECTOR, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td').text
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        try:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text.split("\n")[0]
        except:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split("\n")[0]
            
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
        except:
            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
    

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer:")]//following::td').text
        except:
            try:
                customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
    

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail-Adresse:")]//following::td').text
        except:
            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
    

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse:")]//following::td').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
    
    
        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        tender_criteria_data = tender_criteria()
        try:
            tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"14. Angabe der Zuschlagskriterien")]//following::td[2]').text
        except:
            try:
                tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td').text
            except:
                tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"r) Die Zuschlagskriterien, sofern")]//following::td[2]').text
        tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
        
        try:
            tender_criteria_weight = tender_criteria_data.tender_criteria_title.split("weighting:")[1].split(".")[0].replace(" ",'')
            tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
        except:
            pass        
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number =  1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        
        try:
            lot_description = page_main.find_element(By.XPATH, '//*[@id="printarea"]/div[2]/div[6]/table/tbody/tr[4]/td[2]').text
            lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
        except:
            lot_details_data.lot_description = notice_data.local_title
        
        try:
            contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Beginn der")]//following::td').text
            contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass
    
    
        try:
            contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Ende der")]//following::td').text
            contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass
        

        try:
            lot_details_data.contract_type = page_main.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass
    
        try:
            lot_details_data.lot_grossbudget_lc = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.6) Geschätzter Wert")]//following::td').text
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
    

        try:
            lot_cpvs_data = lot_cpvs()
            lot_cpvs_data.lot_cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td').text.split('-')[0]
            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass


        try:
            lot_criteria_data = lot_criteria()
            lot_criteria_data.lot_criteria_title = tender_criteria_data.tender_criteria_title
            lot_criteria_data.lot_criteria_weight = tender_criteria_data.tender_criteria_weight
            lot_criteria_data.lot_criteria_cleanup()
            lot_details_data.lot_criteria.append(lot_criteria_data)
        except Exception as e:
            logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
            pass
            
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    page_main.back()
    time.sleep(5)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.tableRow.clickable-row.publicationDetail')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ausschreibungen.ls.brandenburg.de/NetServer/"] 
    for url in urls: 
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.tableRow.clickable-row.publicationDetail'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.tableRow.clickable-row.publicationDetail')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.tableRow.clickable-row.publicationDetail')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tr.tableRow.clickable-row.publicationDetail'),page_check))
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
