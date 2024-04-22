from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tn_marches_spn"
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
SCRIPT_NAME = "tn_marches_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'tn_marches_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'AR'
    
    notice_data.currency = 'TND'
    
    notice_data.notice_type = 4
    
    # Onsite Field -آخر أجل لقبول العروض (Deadline for accepting offers)
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d{4}/\d+/\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -الموضوع(the topic)
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -الصنف(item)
    # Onsite Comment -1.replace grabbed keywords with given number("وطني=National=0","دولي =international=1") otherwise pass 0.
    
    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        procurement_method = GoogleTranslator(source='auto', target='en').translate(procurement_method)
        if "international" in procurement_method:
            notice_data.procurement_method = 1
        elif "National" in procurement_method:
            notice_data.procurement_method = 0
        else:
            notice_data.procurement_method = 0
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -تاريخ الاصدار(Release Date)
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(2)").text
        publish_date = re.findall('\d{4}/\d+/\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        attachments_data = attachments()
    # Onsite Field -إعلان طلب العروض(Announcement of request for offers)
    # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute('href')

        attachments_data.file_name = 'Announcement of request for offers'
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -التفاصيل(the details)
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#tablecontent2').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -طلب عروض دولي(International request for offers)
    # Onsite Comment -1.split between " طلب عروض دولي(International request for offers)" and "آخر أجل لقبول العروض".

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, ' td > table:nth-child(2) > tbody > tr:nth-child(3) > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -العدد(the number)
    # Onsite Comment -1.split between " طلب عروض دولي(International request for offers)" and "آخر أجل لقبول العروض".

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, ' table:nth-child(2) > tbody > tr:nth-child(4) > td:nth-child(2)').text
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no = re.findall('\d{5}',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -أجل صلوحية العروض(Validity of offers)
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"أجل صلوحية العروض")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -تاريخ فتح الضروف(Date of opening of envelopes)
    # Onsite Comment -None

    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"تاريخ فتح الضروف")]//following::td[1]').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -طبيعة القسط(Nature of premium)
    # Onsite Comment -1.here "Materials>Other materials" take "Materials".	2.grab the text where ">" is facing means which value is greater. 	3.there is mapping for this field. csv file name as "tn_marches_spn_contract_type.csv" is pulled.
    
    # Onsite Field -طبيعة القسط(Nature of premium)
    # Onsite Comment -1.here "Materials>Other materials" take "Materials".	2.grab the text where ">" is facing means which value is greater.

    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),'طبيعة القسط')]//following::td[1]''').text.split('>')[0].strip()
        contract_type_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        if "materials" in contract_type_actual or "Materials" in contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "works" in contract_type_actual or "Works" in contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "equipment" in contract_type_actual or "Equipment" in contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        else:
            notice_data.notice_contract_type = fn.procedure_mapping(("assets/tn_marches_spn_contract_type.csv",contract_type_actual))
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass


    # Onsite Field -None
    # Onsite Comment -1.if the funding agaency took from the csv than the status of source of fund is "international agency" and if tis oown than pass as it is .		2. 2.csv file is pulled for this field name as "tn_marches_spn_fundingagencies.csv".
    try:
        notice_data.source_of_funds = page_details.find_element(By.XPATH, "//*[contains(text(),'التمويل')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass

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

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'TN'
        customer_details_data.org_language = 'AR'
    # Onsite Field -(المشتري العمومي=Public buyer)
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        

    # Onsite Field -Adresse de réception des offres(Address of delivery)
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse de réception des offres")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -1.take all lots		2.ref_url:"http://www.marchespublics.gov.tn/onmp/appeldoffre/viewappeldoffrefront.php?lang=ar&ID_appeldoffre=90506&"

    try:           
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tablecontent > tbody > tr:nth-child(2) > td > table > tbody > tr > td > table > tbody > tr > td > table:nth-child(3) > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(1) > td > table:nth-child(n)'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, " tr:nth-child(1) > td").text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Objet
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, "tr:nth-child(3)").text.split("Objet ")[1].strip()
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        
        # Onsite Field -الموضوع(the topic)
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, " tr:nth-child(4)").text.split("الموضوع ")[1].strip()
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            
            try:   
                lot_details_data.lot_contract_type_actual = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(2)').text.split('>')[0].strip()
                lot_contract_type_actual = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_contract_type_actual)
                if "materials" in lot_contract_type_actual or "Materials" in lot_contract_type_actual:
                    lot_details_data.contract_type = "Supply"
                elif "works" in lot_contract_type_actual or "Works" in lot_contract_type_actual:
                    lot_details_data.contract_type = "Works"
                elif "equipment" in lot_contract_type_actual or "Equipment" in lot_contract_type_actual:
                    lot_details_data.contract_type = "Supply" 
                else:
                    lot_details_data.contract_type = fn.procedure_mapping(("assets/tn_marches_spn_contract_type.csv",lot_contract_type_actual))
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    url = "http://www.marchespublics.gov.tn/onmp/appeldoffre/listappeldoffrefront.php?lang=ar&URLref_type_procedure=&URLdate_reception_offre_debut=&URLdate_reception_offre_fin=&URLref_lieu_execution=&URLobjet=&URLref_mode_financement=&URLref_secteur=&URLref_type=&Formlist_Sorting=6&Formlist_Sorted=6&&Formlist_Page="
    for page_no in range(1,15):
        url = url+str(page_no)+'#list'
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bordercontent"]/table/tbody/tr')))
            length = len(rows)
            for records in range(4,length-1):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bordercontent"]/table/tbody/tr')))[records]
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
