from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "dk_udbud"
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
SCRIPT_NAME = "dk_udbud"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.main_language = 'DA'
    
    notice_data.script_name = 'dk_udbud'
    
 
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DK'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'DKK'
    
    notice_data.procurement_method = 0
   
    notice_data.notice_type = 4
  
    notice_data.document_type_description = "National tender"
    
    # Onsite Field -Titel
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Annonceret
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Tilbudsfrist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text.split("\n")[0]
        notice_deadline = re.sub("[^\d\-\.]","",notice_deadline)
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y.%H.%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Titel
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#content > div > div.col.main.size10 > div.pad.textcontent > a")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(5)
    except:
        pass
    
    try:
        holder = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.col.main.size10')))
    except:
        pass
    # Onsite Field -None
    # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col.main.size10').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Opgavebeskrivelse")]//following::td[1]').text
        if "Description:" in local_description:
            notice_data.local_description=local_description.split("Description:")[1].strip()
        else:
            notice_data.local_description = local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opgavebeskrivelse
    # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:
        notice_summary_english = notice_data.local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opgavetype
    # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data and Replace following keywords with given respective keywords ('Varekøb = Supply','Tjenesteydelser = Services' ,'Bygge- og anlægsopgaver = Works')

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Opgavetype")]//following::td[1]').text
        if "Varekøb" in notice_contract_type:
            notice_data.notice_contract_type ="Supply"
        elif "Tjenesteydelser" in notice_contract_type:
            notice_data.notice_contract_type ="Service"
        elif "Bygge- og anlægsopgaver" in notice_contract_type:
            notice_data.notice_contract_type ="Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Udvælgelseskriterier
    # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),"Udvælgelseskriterier")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Link til udbudsmateriale
    # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Link til udbudsmateriale")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Skønnet kontraktsum
    # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data and use this url for ref : https://udbud.dk/Pages/Tenders/ShowTender?tenderid=75801

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Skønnet kontraktsum")]//following::td[1]').text.split(" ")[0]
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Skønnet kontraktsum
    # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data and use this url for ref : https://udbud.dk/Pages/Tenders/ShowTender?tenderid=75801

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DK'
        customer_details_data.org_language = 'DA'
        # Onsite Field -Ordregiver
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
       

        # Onsite Field -Adresse
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Kontaktperson
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontaktperson")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Kontakt
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontakt")]//following::td[1]/span[2]').text.split("Telefon: ")[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Kontakt
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontakt")]//following::span[1]/a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Adresse
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse")]//following::td/div/a').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:              
        cpvs_data = cpvs()
        # Onsite Field -CPV kode
        # Onsite Comment -None

        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV kode")]//following::td[1]').text.split("-")[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:              
        tender_criteria_data = tender_criteria()
        # Onsite Field -Tildelingskriterier
        # Onsite Comment -None

        tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Tildelingskriterier")]//following::td[1]').text
        tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)

        # Onsite Field -Tildelingskriterier
        # Onsite Comment -None
        
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
        # Onsite Field -Titel
        # Onsite Comment -None

        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
       
        
        # Onsite Field -Opgavebeskrivelse
        # Onsite Comment -None

        lot_details_data.lot_description = notice_data.notice_summary_english
       
        
        # Onsite Field -Skønnet kontraktsum
        # Onsite Comment -click on 'Luk udbudsdetaljer' to get the data and use this url for ref : https://udbud.dk/Pages/Tenders/ShowTender?tenderid=75801

        try:
            lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
        except Exception as e:
            logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
            pass

        # Onsite Field -Opgavetype
        # Onsite Comment -Replace following keywords with given respective keywords ('Varekøb = Supply','Tjenesteydelser = Services' ,'Bygge- og anlægsopgaver = Works')

        try:
            lot_details_data.contract_type = notice_data.notice_contract_type
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on 'Luk udbudsdetaljer' to get the data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' tr:nth-child(9) > td:nth-child(2) > div > a'):
            attachments_data = attachments()
            # Onsite Field -Dokumenter
        # Onsite Comment -take file_name in textform

        
            attachments_data.file_name = single_record.text.split(".")[0]            
            
             # Onsite Field -Dokumenter
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')            
            
             # Onsite Field -Dokumenter
        # Onsite Comment -split file_type from given selector

            try:
                attachments_data.file_type = single_record.text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Dokumenter
        # Onsite Comment -take file_size if available
        
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
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://udbud.dk/Pages/Tenders/News'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="datagridtenders_1F8CBE3E"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="datagridtenders_1F8CBE3E"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="datagridtenders_1F8CBE3E"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#ContentPlaceHolderMain_ContentPlaceHolderContent_TliNews_BtnNextPage")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="datagridtenders_1F8CBE3E"]/tbody/tr'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
