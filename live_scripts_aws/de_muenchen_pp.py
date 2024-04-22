from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_muenchen_pp"
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

# go to 'Erweiterte Suche' in select data in tab  "Alle Ausschreibungen" + "Vorinformationen" + ["Natioal-EU"/"National"/"EU"]

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_muenchen_pp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_muenchen_pp'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.main_language = 'DE'

    notice_data.notice_type = 3
    # Onsite Field -Ausschreibung
    # Onsite Comment -None
    # Onsite Field -None
    # Onsite Comment -Note:Replace following kegword("National - EU=0","National=0","EU=2")
    if "EU" in url:
        notice_data.procurement_method = 2
    else:
        notice_data.procurement_method = 0
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Erschienen am
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Note:Click on "<tr>tag"
    # Onsite Comment -None

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').click()
        time.sleep(5)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'body > div.page').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        notice_data.notice_no = notice_data.notice_url.split("TOID=")[1].split("-")[0]
    except:
        pass

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Name und Anschrift:
    # Onsite Comment -Note:Take only org_name, dont take address

        customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text.split(",")[0].strip()
    # Onsite Field -Name und Anschrift:
    # Onsite Comment -None
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text.split(",")[1].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
    # Onsite Field -Telefonnummer:
    # Onsite Comment -None
        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    # Onsite Field -E-Mail:
    # Onsite Comment -None
        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
    # Onsite Field -Faxnummer:
    # Onsite Comment -None
        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
    # Onsite Field -Internet:
    # Onsite Comment -None
        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
#     # Onsite Field -2. >> Vergabeverfahren:
#     # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_main.find_element(By.XPATH,'//*[contains(text(),"Vergabeverfahren:")]//following::td[1]').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_muenchen_pp_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::td[2]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -6. Voraussichtlicher Zeitraum der Ausführung: >> ggf. Beginn der Ausführung:
#     # Onsite Comment -Note:Splite after "ggf. Beginn der Ausführung:" and take data

    try:
        tender_contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Voraussichtlicher Zeitraum der Ausführung:")]//following::td[2]').text.split("ggf. Beginn der Ausführung:")[1]
        tender_contract_start_date = re.findall('\d+.\d+.\d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    try:
        tender_contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Voraussichtlicher Zeitraum der Ausführung:")]//following::td[2]').text.split("Fertigstellung der Leistungen bis:")[1]
        tender_contract_end_date = re.findall('\d+.\d+.\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -6. Voraussichtlicher Zeitraum der Ausführung: >> Dauer der Leistung:
#     # Onsite Comment -Note:Splite after "Dauer der Leistung:"

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Voraussichtlicher Zeitraum der Ausführung:")]//following::td[2]').text.split("Dauer der Leistung:")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
# # Onsite Field -None
# # Onsite Comment -Note:if the lot published in "5. Art und voraussichtlicher Umfang der Leistung:", tha take the lots in a Lot loop. refer below url  https:https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b8f9f654d-beb59f108b67433&Category=PriorInformation LotAcualNumber = "Los 1" LotTitle = Los 1 Unterhaltsreiniger

    try:
        lot_text = page_main.find_element(By.XPATH, '//*[contains(text(),"5. Art und voraussichtlicher Umfang der Leistung:")]//following::td[2]').text
        lot_text_list = lot_text.split("Los")
        lot_number = 1
        for single_record in lot_text_list[1:]:
            lot_details_data = lot_details()
    #     # Onsite Field -5. Art und voraussichtlicher Umfang der Leistung:
    #     # Onsite Comment -Note:1)here "Los 1 Unterhaltsreiniger" take "Los 1" as lot_actual_number	2)take all lot_actual_number
            lot_details_data.lot_number = lot_number
            try:
                lot_details_data.lot_actual_number = 'Los'+' '+str(lot_number)
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
    #     # Onsite Field -5. Art und voraussichtlicher Umfang der Leistung:
    #     # Onsite Comment -Note:1)here "Los 1 Unterhaltsreiniger" take "Unterhaltsreiniger" as lot_title	2)take all lot_title
    #     # Ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b8f9f654d-beb59f108b67433&Category=PriorInformation
    
            lot_details_data.lot_title = single_record.split("\n")[0]
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
    #     # Onsite Field -5. Art und voraussichtlicher Umfang der Leistung:
    #     # Onsite Comment -Note:1)after lot_title take lit_description ex.,"Pos. 1 16.000 Liter Handspülmittel" 2)2)take all lot_description

            try:
                lot_description = single_record.split('\n')[1::]
                lot_details_data.lot_description = ''.join(lot_description)
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    page_main.execute_script("window.history.go(-1)")
    time.sleep(5)
    WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-responsive.table-striped.table-hover.tableHorizontalHeader > tbody')))
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://vergabe.muenchen.de/NetServer/PublicationSearchControllerServlet?Searchkey=&function=Search&Category=PriorInformation&TenderLaw=All&TenderKind=All&Authority=&csrt=720839744009011238",
           "https://vergabe.muenchen.de/NetServer/PublicationSearchControllerServlet?Searchkey=&function=Search&Category=PriorInformation&TenderLaw=All&TenderKind=National&Authority=&csrt=720839744009011238",
           "https://vergabe.muenchen.de/NetServer/PublicationSearchControllerServlet?Searchkey=&function=Search&Category=PriorInformation&TenderLaw=All&TenderKind=EU&Authority=&csrt=720839744009011238"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,3):
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
