from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_vmstart_ca"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_vmstart_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

# format-1)in tender_html_element after click on "Vergebene Aufträge >> Liefer- und Dienstleistungen"=="Assigned Orders >> Delivery and Services" and if in type_of_procedure_actual "Öffentliche Ausschreibung"=="public tender" is present. 
# format-2)in tender_html_element after click on "Vergebene Aufträge >> Liefer- und Dienstleistungen"=="Assigned Orders >> Delivery and Services" and if in type_of_procedure_actual remainning keyword.
# format-3)in tender_html_element after click on "Vergebene Aufträge >> Bauleistungen"=="Assigned Orders >> construction work" and if in type_of_procedure_actual "Öffentliche Ausschreibung"=="public tender" or "Verhandlungsverfahren ohne Teilnahmewettbewerb=negotiation procedure without participation competition"   is present.
# format_4)in tender_html_element after click on "Vergebene Aufträge >> Bauleistungen"=="Assigned Orders >> construction work" and if in type_of_procedure_actual remainning keyword .

# note:in tender_html_element after click on "Vergebene Aufträge >> Architekten- und Ingenieurleistungen"=="Assigned Orders >> Architectural and engineering services" in this format currently no data is availabel. so at that point we keep it on hold.

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_vmstart_ca'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'DE'

    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7

    # Onsite Field -Erschienen am
    # Onsite Comment -take publish_date for all format.

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

    # Onsite Field -Ausschreibung
    # Onsite Comment -take local_title for all format.

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass

    # Onsite Field -Verfahrensart
    # Onsite Comment -1.split type_of_procedure_actual after the ", " eg.,"VOB Bund (VHB) - Mannheim, Beschränkte Ausschreibung" here take only "Beschränkte Ausschreibung" 				2.take type_of_procedure_actual for all format.
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.split(",")[1].strip()        
        type_of_procedure_actual = GoogleTranslator(source='de', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_vmstart_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_url = tender_html_element.get_attribute("data-oid")
        notice_data.notice_url = 'https://vergabe.vmstart.de/NetServer/PublicationControllerServlet?function=Detail&TOID='+str(notice_url)+'&Category=ContractAward'
        logging.info(notice_data.notice_url)
        fn.load_page(page_details, notice_data.notice_url,10)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    # Onsite Field -None
    # Onsite Comment -take this document_type_description for all format.
    
    
    try:
        notice_data.notice_text += WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#pagePublicationDetails > div'))).get_attribute("outerHTML")                        
    except Exception as e:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                        
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Vergabenummer:
    # Onsite Comment -1.use format-1 and format-3 to get this.

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.use format-2 and format-4 to get this. 				2.if not availabel then use this selector "div.col-lg-12 > h2" and split notice_no from these field in page main. 				3.grab only if possible.

    # Onsite Field -Tag der Absendung dieser Bekanntmachung:
    # Onsite Comment -1.use format-1 and format-3 to get this.

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.for format-1 only and format-3

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text()," Beschreibung der Beschaffung")]//following::td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        try:
            notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::td[2]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.for format-2 only and format-4 				2.if "Los" keywrd is present then don't grab this in the notice_summary_english. then take local_title in this notice_summary_english.


    # Onsite Field
    # Onsite Comment-1.for format-1 only and format-3
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text()," Beschreibung der Beschaffung")]//following::td').text
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::td[2]').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

    # Onsite Field
    # Onsite Comment:1.for format-2 only and format-4      2.if "Los" keywrd is present then don't grab this in the local_description. then take local_title in this local_description.


    # Onsite Field -None
    # Onsite Comment -1.for format-1 only and format-3 				2.take only amount eg.,"Wert: 49.534,50 EUR"	grab only "49.534,50"

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::td[1]').text.split("Wert:")[1].split("EUR")[0]
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    customer_details_data = customer_details()
    customer_details_data.org_country = 'DE'
    customer_details_data.org_language = 'DE'
    customer_details_data.org_name = org_name

        # Onsite Field -None
        # Onsite Comment -1.for format-1 only and format-3 				2.split org_city between "Postleitzahl / Ort: " and "Land". 		3.take only name.don't grab number i.e postal_code.

    try:
        customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text.split("Postleitzahl / Ort:")[1].split("\n")[0]
    except:
        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Ort der Ausführung:")]//following::td[2]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

# Onsite Field -None
# Onsite Comment -1.for format-2 only and format-4 				2.take only city_name.don't grab number.



# Onsite Field -None
# Onsite Comment -1.for format-1 and format-3 split org_address before "Land:".

    try:
        customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text.split("Postanschrift:")[1].split("Land:")[0]
    except:
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text.split("Postanschrift:")[1].split("Postleitzahl / Ort:")[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

# Onsite Field -None
# Onsite Comment -1.for format-2 only and format-4

# Onsite Field -Telefon:
# Onsite Comment -1.for format-1 only and format-3 				2.split org_phone between "Telefon: " and "E-Mail:".

    try:
        customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text.split("Telefon: ")[1].split("E-Mail:")[0]
    except:
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

# Onsite Field -Telefonnummer:
# Onsite Comment -1.for format-2 only and format-4


# Onsite Field -Fax:
# Onsite Comment -1.for format-1 only and format-3 		2.split org_phone after "Fax:".

    try:
        customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text.split("Fax:")[1].split("\n")[0]
    except:
        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
# Onsite Field -Faxnummer:
# Onsite Comment -1.for format-2 only and format-4

# Onsite Field -E-Mail:
# Onsite Comment -1.for format-1 only and format-3 				2.split org_email between "E-Mail:" and "Fax:".

    try:
        customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text.split("E-Mail:")[1].split("\n")[0].strip()
    except:
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td').text.strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        # Onsite Field -E-Mail:
        # Onsite Comment -1.for format-2 only and format-4


# Onsite Field -None
# Onsite Comment -1.for format-1 only and format-3 				2.split customer_nuts between "NUTS-Code: " and "Kontaktstelle".

    try:
        customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text.split("NUTS-Code: ")[1].split("\n")[0]
    except Exception as e:
        logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
        pass

        # Onsite Field -None
        # Onsite Comment -1.for format-1 only and format-3 				2.take in texy format

    try:
        customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse: (URL)")]//following::a').text
    except:
        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::td').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

# Onsite Field -None
# Onsite Comment -1.for format-2 only and format-4


# Onsite Field -None
# Onsite Comment -1.for format-1 only and format-3 				2.split postal_code between "Postleitzahl / Ort: " and "Land". 				3.take only number in postal_code .don't grab city_name.

    try:
        customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text.split("Postleitzahl / Ort:")[1].split('Land')[0]
    except:
        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Ort der Ausführung:")]//following::td[2]').text.split(" ")[0]
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        # Onsite Field -None
        # Onsite Comment -1.for format-2 only and format-4 				2.take only number.don't grab city_name.

    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td').text.split("-")[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass


    try:
        tender_criteria_data = tender_criteria()
# Onsite Field -None
# Onsite Comment -1.for format-1 only and format-3
        tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text()," Zuschlagskriterien")]//following::td').text
        tender_criteria_data.tender_criteria_title=GoogleTranslator(source='de', target='en').translate(tender_criteria_title)
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
        pass

    lot_details_data = lot_details() 

# Onsite Field -Ausschreibung
# Onsite Comment -1.for format-1 only and format-3

    try:
        lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::td[2]').text
        lot_details_data.lot_title = GoogleTranslator(source='de', target='en').translate(lot_title)
    except:
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        # Onsite Field -None
        # Onsite Comment -1.for format-2 only and format-4 				2.if Los keyword is found then take it in lot_title. take every lot_title seperately.

        # Onsite Field -None
        # Onsite Comment -1.for format-1 only and format-3

    lot_details_data.lot_description = lot_details_data.lot_title
    # Onsite Field -None
    # Onsite Comment -1.for format-2 only and format-4 				2.if Los keyword is found then take it in lot_description. take every lot_description seperately.


    # Onsite Field -None
    # Onsite Comment -1.for format-2 only and format-4

    try:
        contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung ab:")]//following::td').text
        contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
        lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
        pass
        
        # Onsite Field -None
        # Onsite Comment -1.for format-2 only and format-4

    try:
        contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung bis:")]//following::td').text
        contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
        lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
        pass
# Onsite Field -None
# Onsite Comment -1.for format-1 only and format-3 				2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works')
    try:
        contract_type = page_details.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
        if "Dienstleistungen" in contract_type:
            lot_details_data.contract_type ="Service"
        if "Bauauftrag" in contract_type:
            lot_details_data.contract_type ="Works"
    except Exception as e:
        logging.info("Exception in contract_type: {}".format(type(e).__name__))
        pass
    lot_details_data.lot_number = 1
    try:
        award_details_data = award_details()
    # Onsite Field -None
    # Onsite Comment -1.for format-1 only and format-3 					2.bidder_name split before "Postanschrift:"

        try:
            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split("Offizielle Bezeichnung:")[1].split("\n")[0]
        except:
            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::td').text.split("\n")[0]
    # Onsite Field -None
    # Onsite Comment -1.for format-2 only and format-4 					2.take only first line in bidder_name

# Onsite Field -None
# Onsite Comment -1.for format-1 only and format-3 					2.address split between "Postanschrift: " and "Postleitzahl".

        try:
            award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text()," Zuständige Stelle für Rechtsbehelfs-/Nachprüfungsverfahren")]//following::td').text.split("Postanschrift:")[1].split("Postleitzahl / Ort:")[0].strip()
        except:
            try:
                award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split("Postanschrift:")[1].split("Postleitzahl / Ort:")[0].strip()
            except:
                try:
                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::td').text
                except Exception as e:
                    logging.info("Exception in address: {}".format(type(e).__name__))
                    pass

            # Onsite Field -None
            # Onsite Comment -1.for format-1 only and format-3 					2.take ony value eg.,here "Gesamtwert des Auftrags/Loses: 213.043,40 EUR" take only "213.043,40"
        try:
            grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text()," Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::td').text
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

    # Onsite Field -None
    # Onsite Comment -1.for format-1 only and format-3 			2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works')

    try:
        notice_data.notice_contract_type = lot_details_data.contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vergabe.vmstart.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=VOL&Category=ContractAward&thContext=awardPublications","https://vergabe.vmstart.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=VOB&Category=ContractAward&thContext=awardPublications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr'),page_check))
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
