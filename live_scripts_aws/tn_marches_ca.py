from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tn_marches_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tn_marches_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'tn_marches_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'AR'
    notice_data.currency = 'TND'
    notice_data.notice_type = 7
    
    # Onsite Field -تاريخ النتائج(Results history)
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -الصنف(item)
    # Onsite Comment -1.replace grabbed keywords with given number("وطني=National=0","دولي =international=1") otherwise pass 2.

    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if 'وطني' in procurement_method:
             notice_data.procurement_method = 0
        elif 'دولي' in procurement_method:
            notice_data.procurement_method = 1
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -الموضوع(the topic)
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -التفاصيل(the details)
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -1.in tender_html_element click on "#bordercontent > table > tbody > tr > td:nth-child(4) > a" and add this also in notice_text.
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="tablecontent"]').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -عدد الصفقة(Transaction number)
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"عدد الصفقة")]//following::td[1]').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[-1].split('&')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -طريقة الإبرام(Method of conclusion)
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"طريقة الإبرام")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.if the funding agaency took from the csv than the status of source of fund is "international agency" and if tis oown than pass as it is .		2. 2.csv file is pulled for this field name as "tn_marches_ca_fundingagencies.csv".

    try:
        source_of_fundsss = page_details.find_element(By.XPATH, '''//*[contains(text(),'التمويل')]//following::td[1]''').text
        source_of_fundss = GoogleTranslator(source='auto', target='en').translate(source_of_fundsss)
        source_of_funds = fn.procedure_mapping(("assets/tn_marches_ca_fundingagencies.csv",source_of_fundss))
        if source_of_funds.isdigit():
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = source_of_funds
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
        else:
            notice_data.source_of_funds = source_of_funds
            
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject
    # Onsite Comment -None
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Subject')])[2]//following::td[1]''').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'TN'
        customer_details_data.org_language = 'AR'
    # Onsite Field -المشتري العمومي(Public buyer)
    # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"المشتري العمومي")]//following::td[1]').text

    # Onsite Field -Adresse de réception des offres(Address of delivery)
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse de réception des offres")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Department head
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '''//*[contains(text(),'Department head')]//following::td[1]''').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        Lotts_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute("href")                     
        fn.load_page(page_details1,Lotts_url,80)
    except Exception as e:
        logging.info("Exception in Lotts_url: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details1.find_element(By.XPATH, '//*[@id="tablecontent"]').get_attribute("outerHTML")                     
    except:
        pass
    
    #1.in tender_html_element click on "#bordercontent > table > tbody > tr > td:nth-child(4) > a" and grab this data.  
    # Onsite Field -طبيعة القسط(Nature of premium)
    # Onsite Comment -1.here "Materials>Other materials" take "Materials".	2.grab the text where ">" is facing means which value is greater. 				3.there is mapping for this field. csv file name as "tn_marches_ca_contract_type.csv" is pulled.

    try:
        notice_data.contract_type_actual = page_details1.find_element(By.XPATH, '''//*[contains(text(),'طبيعة القسط')]//following::td[1]''').text.split('>')[0].strip()
        contract_type = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        if 'Materials' in contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            notice_data.notice_contract_type = fn.procedure_mapping(("assets/tn_marches_ca_contract_type.csv",contract_type))
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -1.in tender_html_element click on "#bordercontent > table > tbody > tr > td:nth-child(4) > a" and grab this lot_details.

    try:
        lot_number = 1
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'td.content tbody > tr:nth-child(4) > td > table > tbody'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > td').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Objet
        # Onsite Comment -None

    
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td.DataTD').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        
        # Onsite Field -الموضوع(the topic)
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) > td.DataTD').text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -طبيعة القسط(Nature of premium)
        # Onsite Comment -1.here "Materials>Other materials" take "Materials".	2.grab the text where ">" is facing means which value is greater.

            try:
                lot_details_data.lot_contract_type_actual = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(2)').text.split('>')[0].strip()
                contract_type = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_contract_type_actual)
                if 'Materials' in contract_type:
                    lot_details_data.contract_type = 'Supply'
                else:
                    lot_details_data.contract_type = fn.procedure_mapping(("assets/tn_marches_ca_contract_type.csv",contract_type))
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass

            try:
                award_details_data = award_details()
                # Onsite Field -العارض (Viewer)
                # Onsite Comment -None

                award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(5) > td.DataTD').text
                
                # Onsite Field -الثمن (The price)
                # Onsite Comment -None

                try:
                    grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(6) > td.DataTD').text
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc  = float(grossawardvaluelc.replace('.','').replace(',','').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass
                
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
    url = "http://www.marchespublics.gov.tn/onmp/appeldoffre/listresultatappeldoffre.php?lang=ar&URLref_annee=&URLref_type_procedure=&URLref_Semestre=&URLdate_resultat=&URLref_lieu_execution=&URLobjet=&URLref_mode_financement=&URLref_secteur=&URLref_type=&Formlist_Page="

    for page_no in range(1,15):
        url = url+str(page_no)+'#list'
        
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr[2]/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr[2]/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        except:
            logging.info("No new record")
            pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
