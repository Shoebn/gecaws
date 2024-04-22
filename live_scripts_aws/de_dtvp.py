from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_dtvp"
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
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_dtvp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_dtvp'
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    
    
    # Onsite Field -Typ
    # Onsite Comment -VOB/A Ausschreibung --- VOB/A tender "notice Type"-"4" 
    # Sonstige Ausschreibung --- Other tender	 "notice Type"-"4"
    # UVgO Ausschreibung --- UVgO tender  "notice Type"-"4" 
    # UVgO Vergebener Auftrag --- UVgO Awarded order  "notice Type"-"7"  
    # VOB/A Ausschreibung --- VOB/A Order placed  "notice Type"-"7"  
    
    # notices = tender_html_element.get_attribute('innerHTML')
    
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if 'Ausschreibung' in notice_type or 'Ausschreibung' in notice_type or 'Ausschreibung' in notice_type:
            notice_data.notice_type = 4
        elif 'Vergebener Auftrag' in notice_type:
            notice_data.notice_type = 7
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
         # Onsite Field -Angebots- / Teilnahmefrist
        # Onsite Comment -just take from "Ausschreibung / Tendor"

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
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').get_attribute('innerHTML').strip()
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        page_details_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)  a').get_attribute('href')
        id = page_details_url.split('id=')[1]
        id = id.split('%', 1)[0]
        notice_data.notice_url = 'https://www.dtvp.de/Center/public/company/projectForwarding.do?pid=' + id
        logging.info(notice_data.notice_url)
        fn.load_page_expect_id(page_details, notice_data.notice_url, "content", 60)      
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainBox').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ausschreibungs-ID")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:              
        # Onsite Field -Telefon
        # Onsite Comment -None
        Verfahrensangaben_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Verfahrensangaben')]").get_attribute("href")
        fn.load_page(page_details1,Verfahrensangaben_url,180)
        
        customer_details_data = customer_details()
        # Onsite Field -Vergabeplattform / Veröffentlicher
        # Onsite Comment -None
        try:
            customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]').text
        except:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Zur Angebotsabgabe")]//following::div[1]').text.split('Postanschrift')[1].split('UST.-ID')[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_phone = page_details1.find_element(By.CSS_SELECTOR, 'div:nth-child(11) > div > div > div > span').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ort")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse (URL)")]//following::div[1]/a').text
        except:
            try:
                customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse (URL)")]//following::div[1]/a').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

        # Onsite Field -E-mail
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]/span').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.customer_nuts = page_details1.find_element(By.XPATH, '//*[contains(text(),"NUTS Code")]//following::div[1]').text          
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
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
    except:
        try:
            customer_details_data = customer_details()
            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabeplattform / Veröffentlicher:")]//following::span').text
            except:
                customer_details_data.org_name = 'DTVP Veröffentlichung'
                
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Zur Angebotsabgabe")]//following::div[1]').text.split('Postanschrift')[1].split('UST.-ID')[0]
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::span').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Ort")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse (URL)")]//following::div[1]/a').text
            except:
                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse (URL)")]//following::div[1]/a').text
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

            # Onsite Field -E-mail
            # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]/span').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS Code")]//following::div[1]').text          
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

            # Onsite Field -Postleitzahl
            # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postleitzahl")]//following::div[1]/span').text
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
    
    try:
        for single_record in page_details1.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::label[1]'):
            funding_agency = single_record.get_attribute("outerHTML")
            if "checked-element" in funding_agency:
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agency = 1344862
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass 

    
    try:
        notice_data.vat = page_details1.find_element(By.XPATH, '//*[contains(text(),"UST.-ID")]//following::div[1]/span').text
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass
    
    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Auftragsgegenstand")]//following::div/p/b'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.text.split('-')[0].strip()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        try:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
            lot_details_data.lot_description = notice_data.notice_title
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
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
            lot_grossbudget_lc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[8]').text.split('Wert')[1].split('EUR')[0].strip()
            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
    
        try:
            lot_criteria_data = page_details1.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]')
            if 'table' in lot_criteria_data.get_attribute("outerHTML"):
                for lot_crit in lot_criteria_data.find_elements(By.CSS_SELECTOR, 'div'):
                    lot_criteriaa = lot_crit.get_attribute("outerHTML")
                    if "checked-element" in lot_criteriaa :
                        lot_criteria_data = lot_criteria()
                        lot_criteria_title = lot_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) >  td:nth-child(1)').text
                        lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                        lot_criteria_weight = lot_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) > td:nth-child(2) > div > div > div > div').text
                        if '%' in lot_criteria_weight:
                            lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight).replace('%','').strip()
                        else:
                            lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                        lot_criteria_data.lot_criteria_weight = int(lot_crit)
                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
            else:
                for lot_crit in lot_criteria_data.find_elements(By.CSS_SELECTOR, 'label'):
                    lot_criteriaa = lot_crit.get_attribute("outerHTML")
                    if "checked-element" in lot_criteriaa:
                        lot_criteria_data = lot_criteria()
                        lot_criteria_title = lot_crit.text
                        lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass
        
        try:
            notice_text_data = page_details1.find_element(By.XPATH, '/html/body/div[2]/div[4]').text
        except:
            pass
        
        if notice_data.notice_type == 7:
            if "Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde" in notice_text_data:
                text1=notice_text_data.split("Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")[1]
                award_details_data = award_details()
                
                award_details_data.bidder_name = text1.split("Offizielle Bezeichnung")[1].split('\n')[1].split('\n')[0].strip()
                
                award_details_data.address = text1.split("Postanschrift")[1].split("Postleitzahl")[0].replace('\n',' ').strip()
                
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)

     
        try:
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Auftragsgegenstand")]//following::div/p/b'):
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = single_record.text.split('-')[0].strip()
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.est_amount = lot_details_data.lot_grossbudget_lc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
        
    try:
        grossbudgetlc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[8]').text.split('Wert')[1].split('EUR')[0].strip()
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
        pass


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div > div:nth-child(6)'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -Dateiname
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td.truncate-data-cell-nowrap').text.split('.pdf')[0]
            attachments_data.file_type = 'pdf'            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'tr > td > a').get_attribute('href')
        
        # Onsite Field -None
        # Onsite Comment -Größe
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
   
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
                    tender_criteria_weight = tender_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) > td:nth-child(2) > div > div > div > div').text
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
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
page_details1 = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    login_url = 'https://www.dtvp.de/Center/company/login.do?service=https%3A%2F%2Fwww.dtvp.de%2FCenter%2Fsecured%2Fcompany%2Fwelcome.do'
    logging.info('----------------------------------')
    logging.info(login_url)
    
    fn.load_page_expect_xpath(page_main, login_url,'//*[@id="masterForm"]/fieldset/div[1]/label',10)
    try:
        cookies_click =  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ccm-widget"]/div/div[2]/div[2]/button[2]'))).click()
    except:
        pass

    page_main.find_element(By.XPATH,'//*[@id="login"]').send_keys('akanksha.a@dgmarket.com')
    time.sleep(5)
    page_main.find_element(By.XPATH,'//*[@id="password"]').send_keys('mf2vnrZw')
    page_main.find_element(By.XPATH,'//*[@id="masterForm"]/div/input').click()
    login = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content"]/p'))).text
    logging.info(login)
    
    try:
        fn.load_page_expect_xpath(page_details, login_url,'//*[@id="masterForm"]/fieldset/div[1]/label',10)
        try:
            cookies_click =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ccm-widget"]/div/div[2]/div[2]/button[2]'))).click()
        except:
            pass

        page_details.find_element(By.XPATH,'//*[@id="login"]').send_keys('akanksha.a@dgmarket.com')
        time.sleep(5)
        page_details.find_element(By.XPATH,'//*[@id="password"]').send_keys('mf2vnrZw')
        page_details.find_element(By.XPATH,'//*[@id="masterForm"]/div/input').click()
        login = WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content"]/p'))).text
        logging.info(login)
    except:
        pass
    
    try:
        fn.load_page_expect_xpath(page_details1, login_url,'//*[@id="masterForm"]/fieldset/div[1]/label',10)
        try:
            cookies_click =  WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ccm-widget"]/div/div[2]/div[2]/button[2]'))).click()
        except:
            pass

        page_details1.find_element(By.XPATH,'//*[@id="login"]').send_keys('akanksha.a@dgmarket.com')
        time.sleep(5)
        page_details1.find_element(By.XPATH,'//*[@id="password"]').send_keys('mf2vnrZw')
        page_details1.find_element(By.XPATH,'//*[@id="masterForm"]/div/input').click()
        login = WebDriverWait(page_details1, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content"]/p'))).text
        logging.info(login)
    except:
        pass
    
    urls = ['https://www.dtvp.de/Center/common/project/search.do?method=showExtendedSearch&fromExternal=true#eyJjcHZDb2RlcyI6W10sImNvbnRyYWN0aW5nUnVsZXMiOlsiVk9MIiwiVk9CIiwiVlNWR1YiLCJTRUtUVk8iLCJPVEhFUiJdLCJwdWJsaWNhdGlvblR5cGVzIjpbIkV4QW50ZSIsIlRlbmRlciIsIkV4UG9zdCJdLCJkaXN0YW5jZSI6MCwicG9zdGFsQ29kZSI6IiIsIm9yZGVyIjoiMCIsInBhZ2UiOiIxIiwic2VhcmNoVGV4dCI6IiIsInNvcnRGaWVsZCI6IlBST0pFQ1RfUFVCTElDQVRJT05fREFURV9MTkcifQ'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            cookies_click = page_main.find_element(By.CSS_SELECTOR,'button.button.ccm--save-settings.ccm--button-primary.ccm--ctrl-init').click()
        except:
            pass

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
                    time.sleep(10)
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
