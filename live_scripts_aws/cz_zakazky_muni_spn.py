from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cz_zakazky_muni_spn"
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

#Note:click on "+"  to get data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cz_zakazky_muni_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cz_zakazky_muni_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CZ'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CZK'
    
    notice_data.main_language = 'CS'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -Název Režim VZ
    # Onsite Comment -Note:Take a text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Datum zahájení
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Lhůta pro nabídky / žádosti
    # Onsite Comment -None 09.01.2024 10:00

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(4)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
  
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > td > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        page_details.refresh()
        time.sleep(4)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -Note:Take a first data
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#dus > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Systémové číslo:
    # Onsite Comment -Note:If not availavle in source take notice_no from notice_url

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'b:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Druh veřejné zakázky
    # Onsite Comment -Note:Take a first data. 	Note:Replace following keywords with given keywords("Stavební práce=Works","Dodávky=Supply","Služby=Service")

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Druh veřejné zakázky")]//following::b[1]').text
        notice_data.contract_type_actual = notice_contract_type
        if 'Stavební práce' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Dodávky' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Služby' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Název, druh veřejné zakázky a popis předmětu
    # Onsite Comment -None
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Název, druh veřejné zakázky a popis předmětu")]//following::p[1]').text.split('Stručný popis předmětu:')[1].strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Druh řízení
    # Onsite Comment -Note:Take a first data
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Druh řízení')]//following::b[1]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/cz_zakazky_muni_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Předpokládaná hodnota
    # Onsite Comment -Note:Take a first data.    Splite after "Předpokládaná hodnota" this keyword

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Předpokládaná hodnota")]//following::b[1]').text
        netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
        notice_data.netbudgetlc = float(netbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -URL odkazy >> URL adresa
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"URL odkazy")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -Note:Take a first data

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
        # Onsite Comment -Note:Take a first line. Splite after "M.Sc."

        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontakt")]//following::p[1]').text
            if ', e-mail' in contact_person:
                customer_details_data.contact_person=contact_person.split(', e-mail')[0].strip()
            else:
                customer_details_data.contact_person=contact_person.split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Kontakt
        # Onsite Comment -Note:Splite after "tel.:"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontakt")]//following::p[1]').text.split('tel.: ')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Kontakt
        # Onsite Comment -Note:Splite after "e-mail:"e-mail

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontakt")]//following::p[1]').text
            if 'e-mail:' in org_email: 
                customer_details_data.org_email= org_email.split('e-mail: ')[1].strip()
            elif 'e-mail' in org_email: 
                customer_details_data.org_email= org_email.split('e-mail')[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Id profilu zadavatele ve VVZ:
        # Onsite Comment -None

        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Id profilu zadavatele ve VVZ:")]//following::b[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'CZ'
        customer_details_data.org_language = 'CS'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Části veřejné zakázky')))
        page_details.execute_script("arguments[0].click();",lot_click)
    except:
        pass
    
#Ref_url=https://zakazky.muni.cz/contract_display_6995.html
    try:   
        lot_number = 1
        lot_data = page_details.find_element(By.XPATH, '//*[contains(text(),"Části veřejné zakázky")]//following::div[1]')
        for single_record in lot_data.find_elements(By.CSS_SELECTOR, '#body_parts > div > table > tbody > tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Části veřejné zakázky >> Název
        # Onsite Comment -Note:Splite only two word ex.,"Část 1 Inkubátor s CO2 (6 ks)" take only "Část 1"

            try:
                lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
                if '-' in lot_actual_number:
                    lot_details_data.lot_actual_number = lot_actual_number.split('-')[0].strip()
                elif 'část č.' in lot_actual_number:
                    lot_details_data.lot_actual_number = lot_actual_number.split('VZ')[0].strip()
                elif 'Část' in lot_actual_number:
                    lot_actual_number1 = lot_actual_number.split(' ')[1].strip()
                    lot_details_data.lot_actual_number = 'Část'+lot_actual_number1
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Části veřejné zakázky >> Název
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
            try:
                lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_netbudget_lc = re.sub("[^\d\.\,]", "", lot_netbudget_lc).strip()
                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
            
            try:
                notice_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
                fn.load_page(page_details1,notice_url,80)
                logging.info(notice_url)
            except Exception as e:
                logging.info("Exception in notice_url1: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name and description of the subject
        # Onsite Comment -Note:First go to "#body_parts tr > td:nth-child(2) > a" this link than grab the data

            try:
                lot_details_data.lot_description = page_details1.find_element(By.CSS_SELECTOR, 'div.half > p').text.split('Stručný popis předmětu:')[1].strip()
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass 
    
    time.sleep(5)
    try:
        lot_close = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Části veřejné zakázky')))
        page_details.execute_script("arguments[0].click();",lot_close)
        time.sleep(5)
    except:
        pass
    
    try:
        attch_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Zadávací dokumentace')))
        page_details.execute_script("arguments[0].click();",attch_click)
    except:
        pass
    
    try: 
        attach_data = page_details.find_element(By.XPATH, '//*[contains(text(),"Zadávací dokumentace - soubory ke stažení")]//following::div[1]')
        for single_record in attach_data.find_elements(By.CSS_SELECTOR, '#body_doc_zad > div.list > table > tbody > tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -Zadávací dokumentace >> Jméno souboru
        # Onsite Comment -Note:Don't take file extention Zadávací dokumentace - soubory ke stažení
                
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text.replace(attachments_data.file_type,'').strip()
        # Onsite Field -Zadávací dokumentace >> Popis
        # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    time.sleep(5)
    
    try:
        attch_close = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Zadávací dokumentace')))
        page_details.execute_script("arguments[0].click();",attch_close)
        time.sleep(5)
    except:
        pass
    
    try:
        attch_click2 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#a_doc_pub')))
        page_details.execute_script("arguments[0].click();",attch_click2)
    except:
        pass

    try:    
        attach_data1 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Veřejné dokumenty")])[2]//following::div[1]')
        for single_record in attach_data1.find_elements(By.CSS_SELECTOR, '#body_doc_pub > div.list > table > tbody > tr')[1:]:
            data = single_record.text
            if 'Vysvětlení/změny/doplnění zadávací dokumentace' in data:
                pass
            else:
                attachments_data = attachments()

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
            # Onsite Field -Veřejné dokumenty >> Jméno souboru
            # Onsite Comment -Note:Don't take file extention

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text.replace(attachments_data.file_type,'').strip()
            # Onsite Field -Veřejné dokumenty >> Popis
            # Onsite Comment -None

                try:
                    attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in file_description: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field -Veřejné dokumenty >> Velikost
        # Onsite Comment -None

                try:
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.strip()
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)  
        
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    time.sleep(5)
    try:
        attch_close2 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#a_doc_pub')))
        page_details.execute_script("arguments[0].click();",attch_close2)
        time.sleep(5)
    except:
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://zakazky.muni.cz/contract_index.html?type=all&state=all&page='+str(page_no)+"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="centerBlock"]/div/table/tbody'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="centerBlock"]/div/table/tbody')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="centerBlock"]/div/table/tbody')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="centerBlock"]/div/table/tbody'),page_check))
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
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
