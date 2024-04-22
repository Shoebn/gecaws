from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_hessen_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
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
SCRIPT_NAME = "de_hessen_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -format 1 :- if type_of_procedure_actual have keywords like 'open procedure' and format 2 :- if type_of_procedure_actual have keywords like 'restricted tender','negotiated award without competitive tender','negotiated award without participation competition','free hand assignment'
    notice_data.script_name = 'de_hessen_ca'
    notice_data.main_language = 'DE'
  
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2 
    notice_data.notice_type = 7
   
    try:
        document_type_description = page_main.find_element(By.CSS_SELECTOR, 'div > h1').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.mb-3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-5 > p:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art:
    # Onsite Comment -split type_of_procedure_actual from the selector eg :from "VOB, Öffentliche Ausschreibung" take only "Öffentliche Ausschreibung"
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-7  > div:nth-child(1)  > div > div:nth-child(2)").text
        type_of_procedure_actual= GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_hessen_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass   

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'section > div> a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content-section').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung ab:")]//following::td[1]').text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is None:
        return
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -Kurze Beschreibung:
    # Onsite Comment -use this selector for FORMAT 1 and if notice_summary_english is not available then pass local_title as notice_summary_english

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung:")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        pass
 
    # Onsite Field -None
    # Onsite Comment -use this selector for FORMAT 1 and if local_description is not available then pass local_title as local_description
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
    
    
    # Onsite Field -II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)
    # Onsite Comment -None
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Gesamtwert")]//following::td[1]').text.strip().replace('.','').replace(',','')
        notice_data.grossbudgetlc = int(re.findall('\d+',grossbudgetlc)[0])
        notice_data.est_amount = int(re.findall('\d+',grossbudgetlc)[0])
    except:
        try:
            notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)")]//following::td[1]').text
            notice_data.grossbudgetlc = int(re.findall('\d+',grossbudgetlc)[0])
            notice_data.est_amount = int(re.findall('\d+',grossbudgetlc)[0])
        except:
        
            try:
                grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td[1]').text.strip().replace('.','').replace(',','')
                notice_data.grossbudgetlc = int(re.findall('\d+',grossbudgetlc)[0])
                notice_data.est_amount = int(re.findall('\d+',grossbudgetlc)[0])
            except Exception as e:
                logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
                pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
     
        org_name = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(3) > td:nth-child(2)').text
        if 'Offizielle Bezeichnung:' in org_name or '' not in org_name:
            customer_details_data.org_name = org_name.replace('Offizielle Bezeichnung:','').split('\n')[0].strip() 
        elif '' not in org_name:
            customer_details_data.org_name = org_name.split('\n')[0].strip()
        else:
            customer_details_data.org_name ='Vergabeplattform Land Hessen'
       

        # Onsite Field -Name und Adressen
        # Onsite Comment -use this selector for FORMAT 1

        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(3) > td:nth-child(2)').text.split('Postanschrift:')[1].split('NUTS')[0]
        except:
            pass
            # Onsite Field -Name und Anschrift:
            # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
    
        # Onsite Field -Telefonnummer:
        # Onsite Comment -use this selector for FORMAT 2

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('Telefon: ')[1].split('E-Mail')[0] 
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td[1]').text
            except:
                try:
                    org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::td[1]').text.strip()
                    if org_phone !='':
                        customer_details_data.org_phone = org_phone
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field -E-Mail:
        # Onsite Comment -use this selector for FORMAT 1 and split org_email from the given selector take only 'E-Mail:'

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('E-Mail:')[1].split('Fax:')[0].strip().lower().replace('\n','')
        except:
            pass
    
            # Onsite Field -E-Mail:
            # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_email =fn.get_email(page_details.find_element(By.CSS_SELECTOR, '#content-section').get_attribute("outerHTML").strip().lower().replace('\n',''))
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -use this selector for FORMAT 1 and split org_fax from the given selector take only 'Fax:'

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('Fax:')[1] 
        except:
            pass
    
            # Onsite Field -faxnummer:
            # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"faxnummer:")]//following::td[1]').text
            except:
                try:
                    customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::td[1]').text 
                except:
                    try:
                        customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer:")]//following::td[1]').text
                    except Exception as e:
                        logging.info("Exception in org_fax: {}".format(type(e).__name__))
                        pass
    
        # Onsite Field -Internet-Adresse(n)
        # Onsite Comment -use this selector for FORMAT 1

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::a[1]').text
        except:
            try:
                # Onsite Field -Internet
                # Onsite Comment -use this selector for FORMAT 2
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse")]//following::a[1]').text
            except:
                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet")]//following::a[1]').text
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass
    
        # Onsite Field -Name und Adressen
        # Onsite Comment -use this selector for FORMAT 1  split customer_nuts from the given selector take only 'NUTS-Code:'

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('NUTS-Code: ')[1].split('\n')[0]
        except:
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:     
                 
        for cpvs_records in page_details.find_elements(By.XPATH, '//*[contains(text(),"CPV")]//following::td[1]'):
            for cpv in cpvs_records.text.split('\n'):
                single_cpv = re.findall('\d+', cpv)[0]
                if len(single_cpv)>6: 
                    cpvs_data = cpvs()
                    # Onsite Field -CPV-Code Hauptteil
                    # Onsite Comment -use this selector for FORMAT 1

                    cpvs_data.cpv_code = single_cpv
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:      
        # Onsite Field -Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -if in below text written as "Angaben zu Mitteln der Europäischen Union Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird: Nein" than pass the "None" in field name "T.FUNDING_AGENCIES::TEXT" and if "Angaben zu Mitteln der Europäischen Union Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird:YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862)" in field name "T.FUNDING_AGENCIES::TEXT"

        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::td[1]').text
        funding_agency =  GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency.lower():
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency=1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
 
    try:              
        tender_criteria_data = tender_criteria()
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -use this selector for FORMAT 1
        
        try:
            tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]').text
            tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
        except:
            # Onsite Field -Zuschlagskriterien
            # Onsite Comment -use this selector for FORMAT 2
            tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::tr[2]').text
            tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -Los-Nr:
    # Onsite Comment -split lot_actual_number from the given selector take only 'Los-Nr:'
        try:
            lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td[1]').text.split('Los-Nr:')[1]
        except:
            pass
        
        try:
            lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td[1]').text
            lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
        except:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
            
        try:
            lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Beschreibung der Beschaffung")]//following::td[1]').text
            lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
        except:
            lot_details_data.lot_description = notice_data.notice_title
            
        
    
    # Onsite Field -Gesamtwert der Beschaffung (ohne MwSt.)
    # Onsite Comment -None

       
        try:
            lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Gesamtwert")]//following::td[1]').text.strip()
            lot_details_data.lot_grossbudget_lc = int(re.findall('\d+',lot_grossbudget_lc)[0])
        except:
            try:
                lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td[1]').text.strip()
                lot_details_data.lot_grossbudget_lc = int(re.findall('\d+',lot_grossbudget_lc)[0])   
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
    # Onsite Field -Information über die Nichtvergabe
    # Onsite Comment -None
    
   
        try:     
                 
            for cpvs_records in page_details.find_elements(By.XPATH, '//*[contains(text(),"CPV")]//following::td[1]'):
                for cpv in cpvs_records.text.split('\n'):
                    single_cpv = re.findall('\d+', cpv)[0]
                    if len(single_cpv)>6: 
                        lot_cpvs_data = lot_cpvs()
                        # Onsite Field -CPV-Code Hauptteil
                        # Onsite Comment -use this selector for FORMAT 1

                        lot_cpvs_data.lot_cpv_code = single_cpv
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass
        
        try:
            lot_criteria_data = lot_criteria()

            # Onsite Field -II.2.5) Zuschlagskriterien
            # Onsite Comment -None

            lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td[1]').text
            lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
            # Onsite Field -II.2.5) Zuschlagskriterien
            # Onsite Comment -None
            lot_criteria_data.lot_criteria_cleanup()
            lot_details_data.lot_criteria.append(lot_criteria_data)
        except Exception as e:
            logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
            pass
        
        try:
            award_details_data = award_details()
            
            # Onsite Field -Auftragnehmer:
            # Onsite Comment -split bidder_name and take first line as bidder_name from the given selector
            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text()," Auftragnehmer:")]//following::td[1]').text.split('\n')[0]
            # Onsite Field -Auftragnehmer:
            # Onsite Comment -split address and take second and third line as address from the given selector
            try:
                award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text()," Auftragnehmer:")]//following::td[1]').text.split('\n')[1]
            except:
                pass
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        if lot_details_data is not None:
            lot_details_data.lot_number = 1
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://vergabe.hessen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=ContractAward&thContext=awardPublications&Order=desc&OrderBy=Publishing&Max=25'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="searchForm"]/div/div/div/section/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchForm"]/div/div/div/section/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchForm"]/div/div/div/section/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="searchForm"]/div/div/div/section/div'),page_check))
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
    
