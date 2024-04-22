from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_giz"
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
SCRIPT_NAME = "de_giz"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -take data if available in "Veröffentlichungstyp" select "Beabsichtigte Ausschreibung" and in "Vergabeordnung" select "Alle" for gpn in "Veröffentlichungstyp" select "Ausschreibung" and in "Vergabeordnung" select "Alle" for spnin "Veröffentlichungstyp" select "Vergebener Auftrag" and in "Vergabeordnung" select "Alle" fro ca
    notice_data.script_name = 'de_giz'
    notice_data.main_language = 'DE'
  
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -if document_type_description have keyword "Beabsichtigte Ausschreibung" then  notice type will be 2 , "Ausschreibung" then notice type will be 4 , "Vergebener Auftrag" then notice type will be 7 
#     notice_data.notice_type = 4
    
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
         
    # Onsite Field -Typ
    # Onsite Comment -for document_type_description split data from given selector for eg: from "UVgO Beabsichtigte Ausschreibung" take only "Beabsichtigte Ausschreibung" repeat the same for spn and ca.

    try:
        type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        document_type_description =re.split("\s",type_description,1)[1]
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Bezeichnung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Veröffentlicht
    # Onsite Comment -None

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

    # Onsite Field -Angebots- / Teilnahmefrist
    # Onsite Comment -take notice_deadline when document_type_description have keyword "Ausschreibung" only  and take notice_deadline as threshold date 1 year after the publish_date when document_type_description have keyword "Beabsichtigte Ausschreibung"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Aktion
    # Onsite Comment -None

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute("href")
        notice_url = notice_url.split("javascript:openProjectPopup('")[1].split('%')[0]
        notice_data.notice_url = 'https://ausschreibungen.giz.de'+notice_url
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainBox').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ausschreibungs-ID
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ausschreibungs-ID")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    
    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Auftragsgegenstand")]//following::div/p/b'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.text.split('-')[0].strip()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:
        Verfahrensangaben_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Verfahrensangaben')]").get_attribute("href")
        fn.load_page(page_details1,Verfahrensangaben_url,80)
    except:
        pass
    
    try:
        notice_text_data = page_details1.find_element(By.XPATH, '/html/body/div[2]/div[4]').text
    except:
        pass
    
    # Onsite Field -Kurze Beschreibung
    # Onsite Comment -for notice_summary_english click on "Verfahrensangaben" in detail page and if the "Kurze Beschreibung" field is not available pass the local_title in notice_summary_english
    try:
        page_det1_text = page_details1.find_element(By.XPATH, '//*[@id="content"]/div').text
    except:
        pass
    try:
        if 'Kurze Beschreibung' in page_det1_text:
            notice_summary_english = page_details1.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::div[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        else:
            notice_data.notice_summary_english = notice_data.notice_title
        notice_data.local_description = notice_data.notice_summary_english
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
      
    # Onsite Field -UST.-ID
    # Onsite Comment -for vat Verfahrensangaben > "Zur Angebotsabgabe / Teilnahme auffordernde Stelle " or "Auftraggeber"

    try:
        notice_data.vat = page_details1.find_element(By.XPATH, '//*[contains(text(),"UST.-ID")]//following::div[1]/span').text
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
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
    
    # Onsite Field -Geschätzter Wert
    # Onsite Comment -take data in numeric if available in the detail page (if the given selector is not working use the below selector :- '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]' )
    
    try:
        grossbudgetlc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Gesamtwert")]//following::div[9]/span[1]').text.strip()
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace('.','').replace(',','.').strip()) 
        notice_data.est_amount = notice_data.grossbudgetlc
    except:
        try:
            grossbudgetlc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[9]/span[1]').text.strip()
            grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
            notice_data.grossbudgetlc =float(grossbudgetlc.replace('.','').replace(',','.').strip()) 
            notice_data.est_amount = notice_data.grossbudgetlc
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass
                    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
    try:
        type_of_procedure_actual = page_details1.find_element(By.XPATH, '//*[contains(text(),"Verfahrensart")]//following::div/span[1]').text
        notice_data.type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_giz_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Technische und berufliche Leistungsfähigkeit
    # Onsite Comment -take only tick mark(✔) data
    
    try:
        for single_record in page_details1.find_elements(By.XPATH, '//*[contains(text(),"Technische und berufliche Leistungsfähigkeit")]//following::div[1]'):
            eligibility = single_record.get_attribute("outerHTML")
            if "checked-element" in notice_con:
                notice_data.eligibility = single_record.text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -in page detail click on "Verfahrensangaben" for customer detail  Verfahrensangaben > "Zur Angebotsabgabe / Teilnahme auffordernde Stelle " or "Auftraggeber"

    try:              
        customer_details_data = customer_details()
        
    # Onsite Field -Offizielle Bezeichnung
    # Onsite Comment -None

        try:
            customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -Kontaktstelle
    # Onsite Comment -None
    # //*[contains(text(),"Auftraggeber")]//following::div[11]

        try:
            org_addresss = page_details1.find_element(By.XPATH, '//*[contains(text(),"Kontaktstelle")]//following::div[1]/span').text
            if '' in org_addresss:
                org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Auftraggeber")]//following::div[11]').text.split('Postanschrift')[1].split('Telefon')[0]
                org_address1 = org_address.split('\n')
                org_address2 = org_address1[1:8:2]
                customer_details_data.org_address = ",".join(org_address2).replace('\n',' ')
            else:
                customer_details_data.org_address = org_addresss
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
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
            customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postleitzahl")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -zu Händen von
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details1.find_element(By.XPATH, '//*[contains(text(),"zu Händen von")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    # Onsite Field -Telefon
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -E-Mail
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax
    # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Hauptadresse (URL)
    # Onsite Comment -'//*[contains(text(),"Internet-Adresse (URL)")]//following::a[1]' and '//*[contains(text(),"Adresse des Beschafferprofils (URL)")]//following::a[1]' use this selectors if link is available in this field  ]
        try:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse (URL)")]//following::a[1]').text
        except:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse (URL)")]//following::a[1]').text

    # Onsite Field -NUTS Code
    # Onsite Comment -None

        try:
            customer_details_data.customer_nuts = page_details1.find_element(By.XPATH, '//*[contains(text(),"NUTS Code")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
             
# Onsite Field -None
# Onsite Comment -None
    
    try:
        for single_record in page_details1.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::label[1]'):
            funding_agency = single_record.get_attribute("outerHTML")
            if "checked-element" in funding_agency:
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agency = 1344862
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
            else:
                pass
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
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
                    tender_criteria_weight = tender_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) >  td:nth-child(2) > div > div > div > div').text
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
                                              
# Onsite Field -None
# Onsite Comment -IMP NOTE: if the lots are awarded to multipule bidder than select all the bidder name lot wise (ex: https://ausschreibungen.giz.de/Satellite/public/company/project/CXTRYYRY1H7BKJH9/de/processdata?11)
    
    try:
        lot_number = 1
        for single_record in page_details1.find_elements(By.XPATH, '/html/body/div[2]/div[4]/div/span[2]/div/div[3]/div/div/div'):
            lot = single_record.text
    
            if 'Beschreibung der Beschaffung' in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
        # Onsite Field -Bezeichnung     div:nth-child(2) > fieldset
        # Onsite Comment -take lot_title only when the field name "Bezeichnung" is available  if it is not available pass the local_title in lot_title

                try:
                    lot_details_data.lot_title = lot.split('Bezeichnung')[1].split('\n')[1].split('\n')[0]
                except Exception as e:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass

        # Onsite Field -Beschreibung der Beschaffung
        # Onsite Comment -take lot_ description only when the field name "Beschreibung der Beschaffung" is available  if it is not available pass the local_title in lot_ description

                try:
                    lot_details_data.lot_description = lot.split('Beschreibung der Beschaffung')[1].split('\n')[1].split('\n')[0]
                except Exception as e:
                    lot_details_data.lot_description = notice_data.notice_title
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Gesamtwert der Beschaffung (ohne MwSt.)
            # Onsite Comment -take only tick mark(✔) data and  take data in numeric if available in the detail page
                try:  
                    lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Beginn
            # Onsite Comment -take only date from the on site  "Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems > Beginn "

                try:
                    contract_start_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Beginn")]//following::div[1]').text
                    contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Ende
            # Onsite Comment -take only date from the on site  "Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems > Ende "

                try:
                    contract_end_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ende")]//following::div[1]').text
                    contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass
           
                try:
                    for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Weiterer CPV Code")]//following::div[1]/span'):
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = single_record.text.split('-')[0].strip()
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                    pass

            # Onsite Field -None
            # Onsite Comment -take award details for ca only "Verfahren" > "Allgemeine Angaben" and "Auftragsvergabe" and  take data from "Verfahren" > "Allgemeine Angaben" and "Auftragsvergabe" / "Verfahren" > "Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde" only

                if notice_data.notice_type == 7:
                    if "Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde" in notice_text_data:
                        text1=notice_text_data.split("Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")[1]
                        award_details_data = award_details()
                    # Onsite Field -Offizielle Bezeichnung
                    # Onsite Comment -None

                        award_details_data.bidder_name = text1.split("Offizielle Bezeichnung")[1].split('\n')[1].split('\n')[0].strip()
                        
            # Onsite Field -Ort
            # Onsite Comment -'//*[contains(text(),"Postleitzahl")]//following::div[1]' take both this fields in address

                        award_details_data.address = text1.split("Postanschrift")[1].split("Internet-Adresse (URL)")[0].replace('\n',' ').strip()

            # Onsite Field -Angaben zum Wert des Auftrags/Loses (ohne MwSt.)
            # Onsite Comment -take data in numeric if available in the detail page and take only tick mark(✔) data

                        try:
                            grossawardvaluelc = text1.split("Gesamtwert des Auftrags/Loses")[1].split("Angaben zur Vergabe von Unteraufträgen")[0]
                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                            award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace('.','').replace(',','.').strip())  
                        except Exception as e:
                            logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                            pass
                        
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                try:
                    lot_criteria_data = page_details1.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]')
                    if 'table' in lot_criteria_data.get_attribute("outerHTML"):
                        for lot_crit in lot_criteria_data.find_elements(By.CSS_SELECTOR, 'div'):
                            lot_criteriaa = lot_crit.get_attribute("outerHTML")
                            if "checked-element" in lot_criteriaa :
                                lot_criteria_data = lot_criteria()
                                lot_criteria_title = lot_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) >  td:nth-child(1)').text
                                lot_criteria_data.lot_criteria_title = GoogleTranslator(source='de', target='en').translate(lot_criteria_title)
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
                                lot_criteria_data.lot_criteria_title = lot_crit.text
                                lot_criteria_data.lot_criteria_cleanup()
                                lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table.margin-bottom-20'):
            attachments_data = attachments()                        
        # Onsite Field -Dateiname
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        # Onsite Field -Typ
        # Onsite Comment -None
        
            try:
                file_type =  attachments_data.file_name
                if '.pdf' in file_type or '.PDF' in file_type:
                    attachments_data.file_type = 'PDF'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
                                                
        # Onsite Field -Größe
        # Onsite Comment -None

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            
        # Onsite Field -Aktion
        # Onsite Comment -for more attachment click on "Vergabeunterlagen" in detail page (click on "Alle Dokumente als ZIP-Datei herunterladen" to download the document and selector for the button 'div.csx-project-form > div > a' )
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        data = page_details.find_element(By.CSS_SELECTOR,'#subNav > ul').text
        if 'Vergabeunterlagen' in data:
            Vergabeunterlagen_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Vergabeunterlagen')]").get_attribute("href")
            fn.load_page(page_details2,Vergabeunterlagen_url,80)
    
            try:              
                for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'table.margin-bottom-20'):
                    attachments_data = attachments()

                # Onsite Field -Dateiname
                # Onsite Comment -None
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'tbody >tr > td:nth-child(1)').text
                # Onsite Field -Typ
                # Onsite Comment -None
                    try:
                        file_type =  attachments_data.file_name
                        if '.pdf' in file_type or '.PDF' in file_type:
                            attachments_data.file_type = 'PDF'
                        elif 'xlsx' in file_type:
                            attachments_data.file_type = 'xlsx'
                        elif 'doc' in file_type:
                            attachments_data.file_type = 'doc'
                        elif '.zip' in file_type:
                            attachments_data.file_type = 'zip'
                        else:
                            pass
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass
                # Onsite Field -Größe
                # Onsite Comment -None

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'tbody >tr > td:nth-child(4)').text.replace(',','.').strip()
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass
                # Onsite Field -Aktion
                # Onsite Comment -for more attachment click on "Vergabeunterlagen" in detail page (click on "Alle Dokumente als ZIP-Datei herunterladen" to download the document and selector for the button 'div.csx-project-form > div > a' )

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'tbody >tr > td:nth-child(5) > span').click()
                    file_dwn = Doc_Download.file_download()
                    attachments_data.external_url = str(file_dwn[0])
                    
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass
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
page_details2 = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://ausschreibungen.giz.de/Satellite/common/project/search.do?method=searchExtended'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="masterForm"]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="masterForm"]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="masterForm"]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="masterForm"]/table/tfoot/tr/td/div/a[3]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="masterForm"]/table/tbody/tr'),page_check))
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
    page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
