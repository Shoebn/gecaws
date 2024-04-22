from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_had_ca"
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
SCRIPT_NAME = "de_had_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# Note : url is not changeble and that's why  url reference not mentioned in "on site comment"


#how to explore CA details :       1) go to url 
#                                  2) select "Advanced search" option       (left side) 
#                                  3) in the scroll bar select "Supplies/services/works and results of design contests" , click on submit button

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# There are 3 formats for ca  :   format 1) 
#                           	  - Contracted awarded (construction work)

#                                 format 2)
#                           	  - Awarded order (delivery/service)

#                          	      format 3)
#                          	      - Contract award notices - Sectors
#                          	      - Announcement of awarded contracts
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_had_ca'
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
 
     # Onsite Field -Verfahren Leistung
    # Onsite Comment -split the value from bracket ,, Replace following keywords with given respective keywords  ('constuction work = Works' , 'delivery/service = Services ') , (for all format)

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div').text
        if "Bauauftrag" in notice_contract_type or "Bauleistung" in notice_contract_type:
            notice_data.notice_contract_type="Works"
        elif  "Liefer-/Dienstleistung" in notice_contract_type or "Dienstleistungen" in notice_contract_type:
            notice_data.notice_contract_type="Service"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -veröffentlicht am/ Ablauftermin
    # Onsite Comment -this selector is "publish date" of all notice types, publication date and notice_deadline are both mention in same column, upper date is the publication date

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text.split("\n")[0]
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
   
    # Onsite Field -HAD-Ref
    # Onsite Comment -the url will not change, it will pass into main page
    
    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'form > table > tbody > tr'))).click()                    
        notice_data.notice_url = page_main.current_url
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        logging.info('notice_url:-' , notice_data.notice_url)
        notice_data.notice_url = url
    time.sleep(5)
        
   
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_main.find_element(By.CSS_SELECTOR, ' table:nth-child(2) > tbody > tr:nth-child(1) > td').text.split("HAD-Referenz-Nr.:")[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -d)Auftragsgegenstand:
    # Onsite Comment -split the folllowing data from this field,  ( for format 1 and 2)
    
    # Onsite Field -II.1.1)Bezeichnung des Auftrags
    # Onsite Comment -split the folllowing data from this field,  (for format 3)

    try:
        notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Auftragsgegenstand:")[1].split("e)")[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except:
        try:
            notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Bezeichnung des Auftrags")[1].split("II.1")[0].strip()
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
    
    
    try:
        notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Auftragsgegenstand:")[1].split("e)")[0].strip()
    except:
        try:
            notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Kurze Beschreibung")[1].split("II.1")[0].strip()
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

    
    # Onsite Field -d)Auftragsgegenstand:
    # Onsite Comment -split the folllowing data from this field,  ( for format 1 and 2)
    
    # Onsite Field -II.1.4)Kurze Beschreibung
    # Onsite Comment -split the following data from this field, (for format 3)


#     try:
#         notice_summary_english = notice_data.notice_title
#     except Exception as e:
#         logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
#         pass
    
    
    # Onsite Field -IV.1.1)Verfahrensart
    # Onsite Comment -split the following value from  this field , (format 3)

    try:
        notice_data.type_of_procedure_actual = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Verfahrensart")[1].split("IV.1")[0].strip()
        type_of_procedure_actual = GoogleTranslator(source='de', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_had_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split only first text , dont take bracket value (for all format)

    try:
        document_type_description = page_main.find_element(By.CSS_SELECTOR, 'td > h3').text
        notice_data.document_type_description = GoogleTranslator(source='de', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7)Gesamtwert der Beschaffung (ohne MwSt.)
    # Onsite Comment -split the following value from this field (for format 3)

    try:
        est_amount = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Gesamtwert der Beschaffung (ohne MwSt.)")[1].split("II.")[0]
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7)Gesamtwert der Beschaffung (ohne MwSt.)
    # Onsite Comment -split the following value from this field (format 3)

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Il.2.13)Angaben zu Mitteln der Europäischen Union
    # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT" (format 2)

    try:
        funding_agency = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Angaben zu Mitteln der Europäischen Union")[1].split("II.2")[0]
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Auftraggeber/Vergabestelle:
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'DE'
        customer_details_data.org_country = 'DE'
        # Onsite Field -"Auftraggeber/Vergabestelle:"
        # Onsite Comment -you have to split only first line data from this field, (format 1)
        
         # Onsite Field -I.1)Name und Adressen
        # Onsite Comment -split the foloowing data from this field, (format 3)

        
        # Onsite Field -Offizielle Bezeichnung:
        # Onsite Comment -split the following data from this field, (format 2)

        try:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[3]').text
        except:
            try:
                customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Offizielle Bezeichnung:")[1].split("\n")[0]
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
        
        
        # Onsite Field -"Straße:" , "Stadt/Ort:"  , "Land"
        # Onsite Comment -split the following data from this field,  split the data between "Official designation" and "Contact point(s)" field,   (format 1)
        
         # Onsite Field -"Straße:" , "Stadt/Ort:"  , "Land"
        # Onsite Comment -split the following data from this field,  split the data between "Official designation" and "Attn. from" field,   (format 2)
        
        # Onsite Field -None
        # Onsite Comment -split the data between "org_name" and "NUTS code:" field,   (format 3)

        try:
            customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Name und Adressen")[1].split("NUTS-Code:")[0].strip()
        except:
            try:
                customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Straße:")[1].split("Land:")[0].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -Stadt/Ort:
        # Onsite Comment -split the  data between "street" and "country" field,  split only  text value (format 1)
        
        # Onsite Field -Stadt/Ort
        # Onsite Comment -split the  data between "street" and "country" field,  split only  text value (format 2)

        # Onsite Field -I.1)Name und Adressen
        # Onsite Comment -split only  text value (format 3)

        try:
            customer_details_data.org_city = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(11)> td:nth-child(3)').text
        except:
            try:
                customer_details_data.org_city = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Stadt/Ort:")[1].split("\n")[0]
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Land:
        # Onsite Comment -split the data between "Stadt/Ort" and "Kontaktstelle(n)" field,  (format 1
        
        # Onsite Field -Land:
        # Onsite Comment -split the data between "Stadt/Ort" and "Zu Hdn. von" field,  (format 2)
        
        # Onsite Field -I.1)name and addresses
        # Onsite Comment -(format 3)
            
        # Onsite Field -e)Bundesland:
        # Onsite Comment -split the following data from this field, (format 1)

        try:
            customer_details_data.org_state = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Bundesland:")[1].split("f)")[0].strip()
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

        # Onsite Field -Zu Hdn. von
        # Onsite Comment -split the following data from this field, (format 1)
        
        # Onsite Field -Zu Hdn. von
        # Onsite Comment -split the following data from this field, (format 2)

        try:
            customer_details_data.contact_person = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Zu Hdn. von :")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telefon
        # Onsite Comment -get the following data from this field, (format 3)

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon")]').text.split("Telefon:")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_phone = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Telefon:")[1].split("\n")[0]            
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax
        # Onsite Comment -split the data between "Telephone" and "E-Mail" field, (format 1)

        # Onsite Field -Fax
        # Onsite Comment -split the data between "Telephone" and "E-Mail" field, (format 3)

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Fax")]').text.split("Fax:")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_fax = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Fax:")[1].split("\n")[0]            
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail
        # Onsite Comment -split the data between "Fax" and "digital address (URL):" field, (format 1)

        # Onsite Field -E-Mail
        # Onsite Comment -split the data between "Fax" and "Internet-Adresse(n)" field, (format 3)

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]').text.split("E-Mail: ")[1].split("\n")[0].strip()
        except:
            try:
                customer_details_data.org_email = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("E-Mail:")[1].split("digitale Adresse(URL):")[0].split("\n")[0].strip()            
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -digitale Adresse(URL)
        # Onsite Comment -split the data between "Email" and "Vergebener Auftrag nach : §20 (3) VOB/A" field,  ( format 1)

        
        # Onsite Field -Internet-Adresse(n)
        # Onsite Comment -split the below URL from field,  ( format 3)

        try:
            customer_details_data.org_website = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("digitale Adresse(URL):")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        # Onsite Field -Stadt/Ort:
        # Onsite Comment -split the data between "street" and "country" field, split only numeric (5 digit) value (format 1)
        
        # Onsite Field -None
        # Onsite Comment -plit only numeric ( 5 digit ) value (format 3)

        try:
            postal_code = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(11)> td:nth-child(3)').text
            customer_details_data.postal_code = re.sub("[^\d\.\,]","",postal_code)
        except:
            try:
                postal_code = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Stadt/Ort:")[1].split("\n")[0]
                customer_details_data.postal_code = re.sub("[^\d\.\,]","",postal_code)            
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

        # Onsite Field -NUTS-Code:
        # Onsite Comment -split the data from this field, (format 3)

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]').text.split("NUTS-Code:")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Abschnitt II: Gegenstand
# Onsite Comment -None

    try:              
        cpvs_data = cpvs()
        # Onsite Field -II.1.2)CPV-Code Hauptteil:
        # Onsite Comment -split the data from this field, (format 3)

        cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil:")]//following::td[3]').text
        cpvs_data.cpv_code = re.sub("[^\d\.\,]","",cpv_code)
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -II.2.5)award criteria
# Onsite Comment -None

#         tender_cri = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text
        
        # Onsite Field -Kriterium
        # Onsite Comment -split the data from "Kriterium" subfield (format 3)
        
        # Onsite Field -Gewichtung
        # Onsite Comment -split the data from "Gewichtung" subfield (format 3)
    try:              
        tender_criteria_data=tender_criteria()
        
        tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[3]').text
        tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
        
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
#         # Onsite Field -d)Auftragsgegenstand:
#         # Onsite Comment -split the folllowing data from this field, ( for format 1 and 2)
        
#         # Onsite Field -Abschnitt V: Auftragsvergabe
#         # Onsite Comment -split the folllowing data from "		Bezeichnung des Auftrags:" this subfield, ( for format 3)

        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True

#         # Onsite Field -d)Auftragsgegenstand:
#         # Onsite Comment -split the folllowing data from this field, ( for format 1 and 2)
        
#          # Onsite Field -Abschnitt V: Auftragsvergabe
#         # Onsite Comment -split the folllowing data from " Bezeichnung des Auftrags:" this subfield, ( for format 3)

        lot_description = notice_data.notice_title      
        
        # Onsite Field -II.1.7)Gesamtwert der Beschaffung (ohne MwSt.)
        # Onsite Comment -split the following value from this field (format 3)

        try:
            lot_details_data.lot_grossbudget_lc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Auftrags-Nr.
        # Onsite Comment -split the following value from this field (format 3)

        try:
            lot_details_data.lot_actual_number = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Auftragsvergabe")[1].split("Bezeichnung des Auftrags: ")[0].strip()
        except Exception as e:
            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -II.2.3)Erfüllungsort
        # Onsite Comment -split the following value from this field (format 3)

        try:
            lot_nuts = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Erfüllungsort")[1].split("NUTS-Code:")[1].split("Hauptort der Ausführung")[0].strip()
            lot_details_data.lot_nuts = lot_nuts.split(" ")[0]
        except Exception as e:
            logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
            pass

            try:
                lot_cpvs_data = lot_cpvs()

                    # Onsite Field -II.2.2)Weitere(r) CPV-Code(s)
                    # Onsite Comment -split the following data from this field ( format 3)

                lot_cpv_code = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Weitere(r) CPV-Code(s)")[1].split("II.2")[0]
                lot_cpvs_data.lot_cpv_code = re.sub("[^\d\.\,]","",lot_cpv_code)
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

        try:
            award_details_data = award_details()

                # Onsite Field -f)Name des beauftragten Unternehmens:
                # Onsite Comment -split the left (couma seperated) value from this field, (format 1)
            
                 # Onsite Field -f)Name des beauftragten Unternehmens:
                # Onsite Comment -split the data first line data, (format 2)


                # Onsite Field -f)Name des beauftragten Unternehmens:
                # Onsite Comment -split the data from this field, (format 3)

            try:
                bidder_name = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Name des beauftragten Unternehmens:")[1].split("Tag")[0].strip()
                award_details_data.bidder_name = bidder_name.split(":")[1].split("\n")[1].split('\n')[0].strip()
            except:
                bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td[3]').text
                award_details_data.bidder_name = bidder_name.split("\n")[0]
                

                # Onsite Field -Name des beauftragten Unternehmens:
                # Onsite Comment -split the (couma seperated) second and third value data from this field, (format 1)
                
                # Onsite Field -f)Name des beauftragten Unternehmens:
                # Onsite Comment -split the second and third line value data from this field, (format 2)

                # Onsite Field -Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde
                # Onsite Comment -split the data between "org_name" and "NUTS-Code"  (format 3)
                
            try:
                award_details_data.address = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Name des beauftragten Unternehmens:")[1].split("Tag")[0].strip()
            except:
                try:
                    award_details_data.address = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")[1].split("NUTS-Code: ")[0].strip()
                except Exception as e:
                    logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                    pass

                # Onsite Field -V.2.4)Angaben zum Wert des Auftrags/Loses (ohne MwSt.)
                # Onsite Comment -split the data from this field  (format 3)
            try:
                grossawardvaluelc = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text.split("Gesamtwert des Auftrags/Loses: ")[1].split("V.2")[0]
                grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                award_details_data.grossawardvaluelc =float(grossawardvaluelc)
            except Exception as e:
                logging.info("Exception in bidder_name: {}".format(type(e).__name__))
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
    
    page_main.execute_script("window.history.go(-1)")
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://www.had.de/onlinesuche_erweitert.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Erweiterte Suche'))).click()

 

        clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="innerframe"]/form/table[1]/tbody/tr[4]/td[1]/select/optgroup[7]/option[1]'))).click()

 

        clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="innerframe"]/form/table[1]/tbody/tr[4]/td[2]/input'))).click()
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr:nth-child(1) > th:nth-child(1)')))
        except:
            pass
    
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="innerframe"]/table[1]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="innerframe"]/table[1]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," td:nth-child(3) > form > input[type=SUBMIT]:nth-child(26)")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody/tr[2]'),page_check))
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
