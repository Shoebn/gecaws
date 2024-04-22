from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_everga_nrw"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_everga_nrw"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_everga_nrw'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'DE'

        
    #     # Onsite Field -
    #     # Onsite Comment -by clicking on "Ausschreibung / Tendor" take  it as "4", "Beabsichtigte Ausschreibung / Intended Tendor" as "2", "Vergebener Auftrag / Assigned order" as "7" 
    noticess = tender_html_element.get_attribute('innerHTML')
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if 'Ausschreibung' in notice_type:
            notice_data.notice_type = 4
        elif 'Beabsichtigte Ausschreibung' in notice_type:
            notice_data.notice_type = 2
        elif 'Vergebener Auftrag' in notice_type:
            notice_data.notice_type = 7
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass

        # Onsite Field -Angebots- / Teilnahmefrist
        # Onsite Comment -just take from "Ausschreibung / Tendor"
    if notice_data.notice_type !=7:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").get_attribute('innerHTML').strip()
            notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        # Onsite Field -Veröffentlicht
        # Onsite Comment -take Plublication date for all three type "Beabsichtigte Ausschreibung / Intended Tendor,  Ausschreibung / Tendor, Vergebener Auftrag / Assigned order"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").get_attribute('innerHTML').strip()
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

        # Onsite Field -Kurzbezeichnung---abbreviation
        # Onsite Comment - take Local Title for all three type "Beabsichtigte Ausschreibung / Intended Tendor,  Ausschreibung / Tendor, Vergebener Auftrag / Assigned order"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').get_attribute('innerHTML').strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

        # Onsite Field -Typ
        # Onsite Comment -None

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').get_attribute('innerHTML').strip()
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_url = noticess.split("javascript:openProjectPopup('")[1].split("',")[0].strip()
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

        # # Onsite Field -None
        # # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div > div:nth-child(6)'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td.truncate-data-cell-nowrap').text
            attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(3)').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'tr > td > a').get_attribute('href')

            file_type =  attachments_data.file_name
            if '.pdf' in file_type or '.PDF' in file_type:
                attachments_data.file_type = 'PDF'
            else:
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


#     # Onsite Field -None
#     # Onsite Comment -None

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainBox').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()

    # Onsite Field -Ausschreibende Stelle
    # Onsite Comment - "take same for all three type "Beabsichtigte Ausschreibung / Intended Tendor,  Ausschreibung / Tendor, Vergebener Auftrag / Assigned order"

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Auftraggeber / Ausschreibende Stelle')]//following::div").text
        except:
            customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Bezeichnung')]//following::div").text
        
        try:
            Verfahrensangaben_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Verfahrensangaben')]").get_attribute("href")
            fn.load_page(page_details1,Verfahrensangaben_url,80)
        except:
            pass
        
        # Onsite Field -Geschätzter Wert
        # Onsite Comment -take data in numeric if available in the detail page (if the given selector is not working use the below selector :- '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]' )

        try:                                                  
            grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::div[1]').text
            grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
            notice_data.grossbudgetlc =float(grossbudgetlc.replace('.','').replace(',','.').strip()) 
            notice_data.est_amount = notice_data.grossbudgetlc
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass

        # Onsite Field -Telefon Click on  detal page, next click "Verfahrensangaben / procedural detail"
        # Onsite Comment -"take same for all three type "Beabsichtigte Ausschreibung / Intended Tendor,  Ausschreibung / Tendor, Vergebener Auftrag / Assigned order"
        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Kontaktstelle")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse (URL)")]//following::div[1]/a').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass


    # Onsite Field -None
    # Onsite Comment -None

        try:
            customer_details_data.customer_nuts = page_details1.find_element(By.XPATH, '//*[contains(text(),"NUTS Code")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -Click on "Beabsichtigte Ausschreibung / Intended Tendor" next click "Suchen" click on "Aktion / Search" detal page will appear next click "Verfahrensangaben / procedural detail"

        try:
            customer_details_data.contact_person = page_details1.find_element(By.XPATH, '//*[contains(text(),"zu Händen von")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -E-mail
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Ort
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ort")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Postleitzahl
    # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postleitzahl")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -None
    # Onsite Comment -Click on  detal page, next click "Verfahrensangaben / procedural detail", take notice_summary_english for all three type "Beabsichtigte Ausschreibung / Intended Tendor,  Ausschreibung / Tendor, Vergebener Auftrag / Assigned order"

    try:
        notice_summary_english = page_details1.find_element(By.XPATH, '//*[contains(text(),"Art und Umfang der Leistung")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        notice_data.local_description = notice_summary_english
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -just take from "Ausschreibung / Tendor ,Beabsichtigte Ausschreibung / Intended Tendor"

    try:
        notice_data.eligibility = page_details1.find_element(By.XPATH, '//*[contains(text(),"Wirtschaftliche und finanzielle Leistungsfähigkeit")]//following::div[1]/span').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    # Beabsichtigte Ausschreibung / Intended Tendor
    # Onsite Field -UST.-ID
    # Onsite Comment - from detail page click on "Auftraggeber" take for all three type

    try:
        notice_data.vat = page_details1.find_element(By.XPATH, '//*[contains(text(),"UST.-ID")]//following::div[1]/span').text
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass

    try:
        type_of_procedure_actual = page_details1.find_element(By.XPATH, '//*[contains(text(),"Verfahrensart")]//following::div[1]/span').text
        notice_data.type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_nieder_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art des Auftrags
    # Onsite Comment -take only tick mark(✔) data if available and Replace following keywords with given respective keywords ("Dienstleistung" = service , "Lieferleistung"  = supply,"Bauleistung" = work)
    
    try:
        for single_record in page_details1.find_elements(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::label')[:3]:
            notice_con = single_record.get_attribute("outerHTML")
            if "checked-element" in notice_con:
                notice_contract_type = single_record.text
                if 'Dienstleistung' in notice_contract_type:
                    notice_data.notice_contract_type = 'Service' 
                elif 'Lieferleistung' in notice_contract_type:
                    notice_data.notice_contract_type = 'Supply'
                elif 'Bauleistung' in notice_contract_type:
                    notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass


# # Onsite Field -None
# # Onsite Comment -Click on "Beabsichtigte Ausschreibung / Intended Tendor" next click "Suchen" click on "Aktion / Search" detal page will appear next click "Verfahrensangaben / procedural detail"

    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Auftragsgegenstand")]//following::div/p/b'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.text.split('-')[0].strip()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass


# # Onsite Field -None
# # Onsite Comment -Click on "Beabsichtigte Ausschreibung / Intended Tendor" next click "Suchen" click on "Aktion / Search" detal page will appear next click "Verfahrensangaben / procedural detail"

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -None
    # Onsite Comment -None

        
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = lot_details_data.lot_title
        
        
    # Onsite Field -Gesamtwert der Beschaffung (ohne MwSt.)
    # Onsite Comment -take only tick mark(✔) data and  take data in numeric if available in the detail page
        try:                                                         
            lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]').text
            lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
            lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())  
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass

        try:
            contract_start_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Beginn")]//following::div[1]/span').text
            contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

        try:
            contract_end_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ende")]//following::div[1]/span').text
            contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass
        
        try:
            lot_cpvs_data = lot_cpvs()
            lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code
            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass
        
        if notice_data.notice_type ==7:
            try:
                award_details_data = award_details()
        # Onsite Field -None
        # Onsite Comment -select bidder from "Vergebene Aufträge"
                award_details_data.bidder_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]/span').text
        # Onsite Field -Angaben zum Wert des Auftrags/Loses (ohne MwSt.)
        # Onsite Comment -take data in numeric if available in the detail page and take only tick mark(✔) data
                try:                                                           
                    grossawardvaluelc = single_record.find_element(By.XPATH, '//*[contains(text(),"Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::div[6]').text
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace('.','').replace(',','.').strip())  
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        tender_criteria_data = page_details1.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]')
        if 'table' in tender_criteria_data.get_attribute("outerHTML"):
            for tender_crit in tender_criteria_data.find_elements(By.CSS_SELECTOR, 'div'):
                tender_criteriaa = tender_crit.get_attribute("outerHTML")
                if "checked-element" in tender_criteriaa :
                    tender_criteria_data = tender_criteria()
                    tender_criteria_title = tender_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) >  td:nth-child(1)').text
                    tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
                    tender_criteria_weight = tender_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) >  td:nth-child(2) > div > div > div > div').text #.split(" ")[-1]
                    if '%' in tender_criteria_weight:
                        tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight).replace('%','').strip()
                    else:
                        tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
        else:
            for tender_crit in tender_criteria_data.find_elements(By.CSS_SELECTOR, 'label'):
                tender_criteriaa = tender_crit.get_attribute("outerHTML")
                if "checked-element" in tender_criteriaa:
                    tender_criteria_data = tender_criteria()
                    tender_criteria_title = tender_crit.text
                    tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
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
    urls = ['https://www.evergabe.nrw.de/VMPCenter/common/project/search.do?method=showExtendedSearch&fromExternal=true#eyJjcHZDb2RlcyI6W10sImNvbnRyYWN0aW5nUnVsZXMiOlsiVk9MIiwiVk9CIiwiVlNWR1YiLCJTRUtUVk8iLCJPVEhFUiJdLCJwdWJsaWNhdGlvblR5cGVzIjpbIkV4QW50ZSIsIlRlbmRlciIsIkV4UG9zdCJdLCJkaXN0YW5jZSI6MCwicG9zdGFsQ29kZSI6IiIsIm9yZGVyIjoiMCIsInBhZ2UiOiIxIiwic2VhcmNoVGV4dCI6IiIsInNvcnRGaWVsZCI6IlBST0pFQ1RfUFVCTElDQVRJT05fREFURV9MTkcifQ'] 
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,100):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div/div/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/table/tbody/tr')))
                length = len(rows)
                
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                                           
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="nextPage"]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(3)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div/div/div/table/tbody/tr'),page_check))
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
