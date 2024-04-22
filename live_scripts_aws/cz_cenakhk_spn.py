from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cz_cenakhk_spn"
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


#Note:click on "+"  to get data
#Note:Click on this "všechny zakázky" for view pages numbers


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cz_cenakhk_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'cz_cenakhk_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CZ'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'CZK'
    notice_data.main_language = 'CS'
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:if file_name have keyword like "addition" or "change of documentation" or "correction" then notice_type will be 16
    notice_data.notice_type = 4
    
    # Onsite Field -Název Režim VZ
    # Onsite Comment -Note:Take a text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Datum zahájení
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Lhůta pro nabídky / žádosti
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#dus > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Systémové číslo:
    # Onsite Comment -None
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'b:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Druh veřejné zakázky
    # Onsite Comment -Note:Take a first data 	Note:Replace following keywords with given keywords("Stavební práce=Works","Dodávky=Supply","Služby=Service")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Druh veřejné zakázky")]//following::b[1]').text
        if 'Služby' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Stavební práce" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Dodávky" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Název, druh veřejné zakázky a popis předmětu")]//following::p[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Druh řízení
    # Onsite Comment -Note:Take a first data
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),"Druh řízení")]//following::b[1]''').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/cz_cenakhk_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass  
    
    # Onsite Field -Předpokládaná hodnota
    # Onsite Comment -Note:Take a first data.    Splite after "Předpokládaná hodnota" this keyword

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '(//*[contains(text(),"Předpokládaná hodnota")]//following::b[1])[1]').text
        netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
        notice_data.netbudgetlc =float(netbudgetlc.replace(' ','').strip())
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -None
#Ref_url=https://zakazky.cenakhk.cz/contract_display_10380.html

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#evaluation tr')[1:-1]:
            tender_criteria_data = tender_criteria()
        # Onsite Field -Hodnocení nabídek >> Kritéria hodnocení >> Název
        # Onsite Comment -None

            tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        # Onsite Field -Hodnocení nabídek >> Kritéria hodnocení >> Váha
        # Onsite Comment -None

            try:
                tender_criteria_weight = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split('%')[0].strip()
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
        customer_details_data = customer_details()
    # Onsite Field -Úřední název
    # Onsite Comment -Note:Take a first data

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Úřední název")]//following::b[1]').text

    # Onsite Field -Poštovní adresa
    # Onsite Comment -Note:Take a first data

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Poštovní adresa")]//following::b[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Místo plnění
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Místo plnění")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Kontakt
    # Onsite Comment -Note:Take a first line

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontakt")]//following::p[1]').text.split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Kontakt
    # Onsite Comment -Note:Take a second line

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontakt")]//following::p[1]').text.split('mail:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'CZ'
        customer_details_data.org_language = 'CS'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        lotts_clk = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_subject_items'))).click()
        time.sleep(2)
    except:
        pass
    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#body_subject_items div.list tbody tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Položky předmětu >> Název
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

            try:
                lot_cpvs_data = lot_cpvs()

                # Onsite Field -Položky předmětu >> CPV kód
                # Onsite Comment -None

                lot_cpvs_data.lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('-')[0].strip()
                # Onsite Field -Položky předmětu >> Doplňkové kódy
                # Onsite Comment -Note:If available than take                   
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lotts_close = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_subject_items.revealed'))).click()
        time.sleep(2)
    except:
        pass
    
    try:
        attachments_clk = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_doc_zad'))).click()
        time.sleep(2)
    except:
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#body_doc_zad  tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -Zadávací dokumentace >> Jméno souboru
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text.split(attachments_data.file_type)[0].strip()
        # Onsite Field -Zadávací dokumentace >> Popis
        # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Zadávací dokumentace >> Velikost
        # Onsite Comment -None

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Zadávací dokumentace >> Jméno souboru
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
        pass
                                                                                                                    
    try:
        attachments_clk_close = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_doc_zad.revealed'))).click()
        time.sleep(2)
    except:
        pass  
    
    try:
        attachments1_clk = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_dd'))).click()
        time.sleep(2)
    except:
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#body_dd tr'):
            attachments_data = attachments()
        # Onsite Field -Vysvětlení, doplnění, změny zadávací dokumentace >> Předmět
        # Onsite Comment -None
        #Rrh_url=https://zakazky.cenakhk.cz/contract_display_10423.html

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute('href')
        # Onsite Field -Vysvětlení, doplnění, změny zadávací dokumentace >> Druh zprávy
        # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
        pass
    
    try:
        attachments1_clk_close = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_dd.revealed'))).click()
        time.sleep(2)
    except:
        pass
    
    
     # Onsite Field -URL odkazy>>URL adresa
    # Onsite Comment -None
    try:
        add_ten_url = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_urls'))).click()
        time.sleep(2)
    except:
        pass

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    try:
        add_ten_url_close = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#a_urls.revealed'))).click()
        time.sleep(2)
    except:
        pass
    
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://zakazky.cenakhk.cz/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="use"]/div/table/tbody')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="use"]/div/table/tbody')))[records]
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
