from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_whitelabel_ca"
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
SCRIPT_NAME = "de_whitelabel_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# first go to URL : "https://whitelabel.vergabe24.de/index.php?id=870&site=viewSearchResults&view=VA"
# to explore CA details go to "orders placed" option (In local language : "Vergebene Aufträge")
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Reference URL for 2 formats 

# ref URL 1 : https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009
# ref URL 2 : https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_whitelabel_ca'
    
    notice_data.main_language = 'DE'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
  
    notice_data.notice_type = 7

    
    # Onsite Field -Art der Leistung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.td-art-der-leistung').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
#     
    # Onsite Field -Veröffentlicht
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tbody > tr > td.td-veroeffentlicht").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

      # Onsite Field -None
    # Onsite Comment -there is no anchor link when we do the inspect element,

    try:
        url=tender_html_element.get_attribute('onclick')
        url1=url.split("id=")[-1]
        notice_data.notice_url='https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid='+str(url1)
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > #detailText').get_attribute("outerHTML")                     
    except:
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::span[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        notice_data.local_description=notice_data.local_title
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
         
    
     # Onsite Field -split the notice number from "Referenznummer der Bekanntmachung:" field name, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags:")]//following::span[1]').text.split(":")[-1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)   Wert
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::span[1]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        est_amount =est_amount.replace('.','')
        notice_data.est_amount = float(est_amount.replace(',','.').strip())   
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -IV.1.1) Verfahrensart "C:/Users/samiksha-shinde/assets/de_whitelabel_ca_procedure.csv"
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"
#     import pdb;pdb.set_trace()
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Verfahrensart")]//following::span[1]').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_whitelabel_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.3) Art des Auftrags
    # Onsite Comment -Replace following keywords with given respective keywords ('Dienstleistungen = Services ', 'Bauauftrag = Works', 'Ausführung von Bauleistungen = works'),  ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::span[1]').text
        if "Dienstleistungen" in notice_contract_type:
            notice_data.notice_contract_type='Service'
        elif "Bauauftrag" in notice_contract_type or "Ausführung von Bauleistungen" in notice_contract_type:
            notice_data.notice_contract_type='Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -V.2) Auftragsvergabe
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsvergabe ")]//following::p[2]').text.split(") ")[1]
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.2.13) Angaben zu Mitteln der Europäischen Union
    # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"      ,ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13)")]//following::span[1]').text.split(":")[1]
        funding_agencies1 = GoogleTranslator(source='auto', target='en').translate(funding_agencies)
        if "Yes" in funding_agencies1 or "yes" in funding_agencies1:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency=1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
        
#     # Onsite Field -VI.5) Tag der Absendung dieser Bekanntmachung:
#     # Onsite Comment -None

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung")]//following::span[1]').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'

#         # Onsite Field -Name und Anschrift:
#         # Onsite Comment -take only first line, split org_name only from this field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7024126"

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split("Offizielle Bezeichnung: ")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::span[1]').text.split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -Name und Adressen   Offizielle Bezeichnung:
#         # Onsite Comment -split org_name only from  "Name und Adressen   Offizielle Bezeichnung:" this field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"
 
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split("NUTS-Code:")[0]
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text.split("Telefonnummer:")[0]
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass       
        
#         # Onsite Field -Name und Anschrift:
#         # Onsite Comment -split the last text value from the given xpath, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split("Postleitzahl / Ort: ")[1].split("Land:")[0]
        except:
            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text.split("\n")[-1].split(" ")[1] 
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -E-Mail:
#         # Onsite Comment -split the following data from this field,

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split("E-Mail: ")[1].split("\n")[0].strip()
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::span[1]').text.strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
            
#         # Onsite Field -Telefonnummer:
#         # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split("Telefon: ")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -Faxnummer:
#         # Onsite Comment -split the data between "E-Mail:" and "Internet" field , reference url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split("Fax: ")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -NUTS-Code
#         # Onsite Comment -split the data between "Land:" and "Telefon:" field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::span[1]').text.split("NUTS-Code: ")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Name und Anschrift:
#         # Onsite Comment -split the last (5 digit) numeric value from this xpath, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

        try:  
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split("Postleitzahl / Ort: ")[1].split("\n")[0].split(" ")[0]
        except:
            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text.split("\n")[-1].split(" ")[0]
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -Internet:
#         # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::a[1]').text
        except:
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::span[1]').text.split("(URL) ")[1]
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:                      
        # Onsite Field -II.1.2) CPV-Code Hauptteil
        # Onsite Comment -split the first value from this xpath, url ref: "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

        cpvs_data = cpvs()
        cpvs_data.cpv_code=page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::span[1]').text.split("-")[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -if  "II.2.5) Zuschlagskriterien   Qualitätskriterium" this field not exist in lot section then we can  take as a tender_criteria details

    try:              
        next1=page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::span[1]').text.split("Preis")[0].strip()
        if "Name" in next1: 
            data=next1.split("Name:")
            for single_record1 in data[1:]:   
                tender_criteria_data = tender_criteria()
    # #         # Onsite Field -Name:
    # #         # Onsite Comment -title and weight both are mentioned in same line but only take name as a title , split the data from "Name:" field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

                tender_criteria_title = single_record1.split(",")[0].strip()
                tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)

    # #         # Onsite Field -Gewichtung
    # #         # Onsite Comment -title and weight both are mentioned in same line but only take data from "Gewichtung" field as a tender_criteria_weight , split the data from "Gewichtung" field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

                tender_criteria_weight = single_record1.split(":")[-1].replace(",","").strip()
                tender_criteria_data.tender_criteria_weight=int(tender_criteria_weight)

                if next1 != "" or next1 != None or next1 != ' ':
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    
    try:
        notice_text1= page_details.find_element(By.CSS_SELECTOR, 'div > #detailText').text
        if "II.2.1) Bezeichnung des Auftrags:" in notice_text1:
            data1=notice_text1.split("II.2.1) Bezeichnung des Auftrags: ")
            lot_number=1
            for single_record1 in data1[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number

                lot_details_data.lot_actual_number = single_record1.split("\n")[1].split("\n")[0]

                lot_title = single_record1.split("\n")[0].strip()
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)


                lot_description = single_record1.split("Beschreibung der Beschaffung ")[1].split("\n")[0]
                lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
        
                try:
                    lot_details_data.lot_nuts = single_record1.split("NUTS-Code:   ")[1].split("\n")[0]
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass


                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = single_record1.split("CPV-Code Hauptteil: ")[1].split("\n")[0].split("-")[0]
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
            
                try:
                    if lot_title in notice_text1:
                        award_details_data = award_details()
                        data2=notice_text1.split(lot_title)[2]
                        award_details_data.bidder_name = data2.split("Offizielle Bezeichnung:")[1].split("\n")[0].strip()
                        
                        try:
                            address =data2.split(" Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")[1]
                            address1 = address.split("\n")[1:5]
                            award_details_data.address=" ".join(address1)
                        except Exception as e:
                            logging.info("Exception in address: {}".format(type(e).__name__)) 
                            pass
                        
                        try:
                            initial_estimated_value = data2.split("des Auftrags/des Loses: ")[1].split("\n")[0]
                            initial_estimated_value = re.sub("[^\d\.\,]","",initial_estimated_value)
                            initial_estimated_value=initial_estimated_value.replace('.','')
                            award_details_data.initial_estimated_value =float(initial_estimated_value.replace(',','.').strip())   
                        except Exception as e:
                            logging.info("Exception in initial_estimated_value: {}".format(type(e).__name__)) 
                            pass 
                        
                        try:
                            agrossawardvaluelc = data2.split("Gesamtwert des Auftrags/Loses:")[1].split("\n")[0]
                            grossawardvaluelc = re.sub("[^\d\.\,]","",agrossawardvaluelc)
                            grossawardvaluelc=grossawardvaluelc.replace('.','')
                            award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','.').strip())
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
                lot_number+=1             
        else:
            lot_details_data = lot_details()
            lot_details_data.lot_number=1
            lot_details_data.lot_title =notice_data.notice_title
            notice_data.is_lot_default = True
            lot_details_data.lot_description=notice_data.notice_title  
            
            try:
                award_details_data = award_details()
                
                try:
                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::span').text.split("\n")[0].strip()   
                except:
                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) ")]//following::span[1]').text.split("\n")[0].split("Offizielle Bezeichnung: ")[1]
                    
                
                try:
                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) ")]//following::span[1]').text.split("NUTS-Code")[0]
                except:
                    try:
                        award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::span').text.split("\n")[1].strip() 
                    except Exception as e:
                        logging.info("Exception in address: {}".format(type(e).__name__)) 
                        pass 
            
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__)) 
                pass
            
            try:
                initial_estimated_value = notice_text1.split("des Auftrags/des Loses: ")[1].split("\n")[0]
                initial_estimated_value = re.sub("[^\d\.\,]","",initial_estimated_value)
                initial_estimated_value=initial_estimated_value.replace('.','')
                award_details_data.initial_estimated_value =float(initial_estimated_value.replace(',','.').strip())   
            except Exception as e:
                logging.info("Exception in initial_estimated_value: {}".format(type(e).__name__)) 
                pass
            
            try:
                agrossawardvaluelc = notice_text1.split("Gesamtwert des Auftrags/Loses:")[1].split("\n")[0]
                grossawardvaluelc = re.sub("[^\d\.\,]","",agrossawardvaluelc)
                grossawardvaluelc=grossawardvaluelc.replace('.','')
                award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__)) 
                pass

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
    urls = ["https://whitelabel.vergabe24.de/index.php?id=870&site=viewSearchResults&view=VA"] 
    for url in urls:
        fn.load_page(page_main, url, 180)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH,'//*[@id="wrapperResult"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="wrapperResult"]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="wrapperResult"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
