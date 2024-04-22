from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "nl_aanbe"
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
SCRIPT_NAME = "nl_aanbe"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'nl_aanbe'
    
    notice_data.main_language = 'NL'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -take only keyword inside the brackets() like 'Aankondiging= Announcement','Gunningsbeslissing= Award decision','Gerectificeerd = Corrected','Vooraankondiging= Pre-announcement'

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dateInfo > span > span').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
        if "Announcement" in notice_data.document_type_description or "Market consultation" in notice_data.document_type_description:
            notice_data.notice_type = 4 
        elif "Award decision" in notice_data.document_type_description:
            notice_data.notice_type = 7
        elif "Corrected" in notice_data.document_type_description:
            notice_data.notice_type = 16
        elif "Pre-announcement" in notice_data.document_type_description:
            notice_data.notice_type = 2
        else:
            pass

    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div>div:nth-child(3)>a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split publish_date from the given selector

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span.date").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.link > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:  
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#didomi-notice-agree-button > span")))
        page_details.execute_script("arguments[0].click();",click)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.col-sm-3 > ul > li:nth-child(1)')))
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-9.publication > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
#     Onsite Field -Termijn voor ontvangst van inschrijvingen of deelnemingsaanvragen
#     Onsite Comment -take notice_deadline for notice_type 4 and 16 only and take notice_deadline as threshold date 1 year after the publish_date for notice_type 2 

    try:
        if  notice_data.notice_type == 16:
            notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Termijn voor ontvangst van inschrijvingen of deelnemingsaanvragen")]//following::p[2]').text
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        notice_data.notice_deadline = threshold
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
#     Onsite Field -Referentienummer:
#     Onsite Comment -split notice_no from the given selector

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Referentienummer:")]').text.split("Referentienummer:")[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
#     Onsite Field -Beschrijving van de aanbesteding:
#     Onsite Comment -if notice_summary_english is not available then pass local_title as notice_summary_english

    try:
        notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-9.publication > div').text.split("Korte beschrijving")[1].split("Afdeling VI: ")[0].split("II.")[0].strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        notice_data.notice_summary_english = notice_data.notice_title
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
        
#     Onsite Field -Beschrijving van de aanbesteding:
#     Onsite Comment -if local_description is not available then pass local_title as local_description 
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-9.publication > div').text.split("Korte beschrijving")[1].split("II.")[0].strip()
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Totale waarde van de aanbesteding")]//following::p[1]').text
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace(',','.').strip())
    except:
        try:
            grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Prijsverhogingen")]//following::p[2]').text
            grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
            notice_data.grossbudgetlc =float(grossbudgetlc.replace(',','.').strip())
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Totale waarde van de aanbesteding
    # Onsite Comment -'//*[contains(text(),"Prijsverhogingen")]//following::p[2]' take dis selector for notice_type 16

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Type opdracht
    # Onsite Comment -Replace following keywords with given respective keywords ('Werken = Works','Diensten = Supply','Leveringen = Supply')

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type opdracht")]//following::p[1]').text
        if "Werken" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "Diensten" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Leveringen" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    
     # Onsite Field -Datum van verzending van deze aankondiging
    # Onsite Comment -None

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Datum van verzending van deze aankondiging")]//following::dd[1]').text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
  
    # Onsite Field -Procedure
    # Onsite Comment -Click on "Algemeen" to get type_of_procedure_actual
    try:
        url = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-3 > ul > li:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details1,url,80)
    except:
        pass
    
    try:
        click = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#didomi-notice-agree-button > span")))
        page_details1.execute_script("arguments[0].click();",click)
    except:
        pass
    
    try:
        WebDriverWait(page_details1, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.col-sm-3 > ul > li:nth-child(3)')))
    except:
        pass
    
    try:
        notice_data.type_of_procedure_actual = page_details1.find_element(By.XPATH, '//*[contains(text(),"Procedure")]//following::div[1]').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("C:/Users/Shoeb Navalur/assets/nl_aanbe_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Totale waarde van de aanbesteding
    # Onsite Comment -'//*[contains(text(),"Prijsverhogingen")]//following::p[2]' take dis selector for notice_type 16
# Onsite Field -Aanbestedende dienst/instantie
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'NL'
        customer_details_data.org_country = 'NL'
        
        # Onsite Field -Officiële benaming:
        # Onsite Comment -None
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tenderrelation').text
        
        
        # Onsite Field -Postadres:
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postadres:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Postcode:
        # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Plaats van uitvoering
        # Onsite Comment -Click on "Algemeen" to get org_city

        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Plaats van uitvoering")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contactpersoon:
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contactpersoon:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -Telefoon:
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -E-mail:
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Fax:
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax: ")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        # Onsite Field -Internetadres(sen)
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internetadres(sen)")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Hoofdactiviteit
        # Onsite Comment -None

        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdactiviteit")]//following::ul[1]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
        
        if customer_details_data.org_name!= None:
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
        # Onsite Field -Inlichtingen over middelen van de Europese Unie
        # Onsite Comment -if in below text written as "Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT" "Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: yes" than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

    try:
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Inlichtingen over middelen van de Europese Unie")]//following::p[1]').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency).split(":")[1]
        if 'yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass
        
# Onsite Field -None
# Onsite Comment -Click on "Algemeen" to get the cpv codes

    try:              
        for single_record in page_details1.find_elements(By.XPATH, '//*[contains(text(),"CPV Codes")]//following::div[1]'):
            cpvs_data = cpvs()
            
        # Onsite Field -CPV Codes
        # Onsite Comment -Click on "Algemeen" to get the cpv codes
            try:
                cpv_code = single_record.text.split(":")[0]
                cpvs_data.cpv_code = re.sub("[^\d]","",cpv_code)
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Gunningscriteria
# Onsite Comment -None

    try:  
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Gunningscriteria")]//following::p'):
            
            if 'Kwaliteitscriterium' in single_record.text or 'Kostencriterium' in single_record.text or "Prijs" in single_record.text:
                tender_criteria_data = tender_criteria()
                tender_criteria_title = single_record.text.replace('Kwaliteitscriterium\nNaam:','')
                tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
                tender_criteria_weight = single_record.text.split('Weging:')[1].split('\n')[0]
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Beschrijving
# Onsite Comment -for lots info ref this link : 'https://aanbestedingskalender.nl/projecten/14924551/publicaties/183804231'

    try:              
        lot_details_data = lot_details()
        
        # Onsite Field -Perceel nr.:
        # Onsite Comment -split lot_number from the given selector

        try:
            lot_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Perceel nr.:")]').text.split("Perceel nr.:")[1]
            lot_number = re.sub("[^\d]","",lot_number)
            lot_details_data.lot_number = int(lot_number)
        except Exception as e:
            lot_details_data.lot_number = 1
            logging.info("Exception in lot_number: {}".format(type(e).__name__))
            pass
        
        try:
            lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Perceel nr.:")]').text.split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Benaming
        # Onsite Comment -if lot_title is not available then pass local_title as lot_title 

        try:
            lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Benaming")]//following::p[1]').text
            lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
            lot_details_data.lot_title=lot_title
        except Exception as e:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Beschrijving van de aanbesteding:
        # Onsite Comment -if lot_description is not available then pass local_description as lot_description

        try:
            text=page_details.find_element(By.XPATH, '/html/body/div[4]/div[1]/div[2]/div/div[3]/div').text
            lot_description=fn.get_string_between(text,'Beschrijving van de aanbesteding:','Gunningscriteria')
            lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
        except Exception as e:
            lot_description = notice_data.local_description
            lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Geraamde waarde
        # Onsite Comment -None

        try:
            lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde")]//following::p[1]').text
            lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
            lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace(',','.').strip())
        except Exception as e:
            lot_details_data.lot_grossbudget_lc =notice_data.grossbudgetlc 
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass

    # Onsite Field -Type opdracht
    # Onsite Comment -Replace following keywords with given respective keywords ('Werken = Works','Diensten = Supply','Leveringen = Supply')

        try:
            lot_details_data.contract_type = notice_data.notice_contract_type
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass

    # Onsite Field -Looptijd in maanden:
    # Onsite Comment -split contract_duration from the given selector

        try:
            lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd in maanden:")]').text.split("Looptijd in maanden:")[1]
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

    # Onsite Field -Aanvang:
    # Onsite Comment -take 'Aanvang:' as contract_start_date from the given selector

        try:
            contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvang: ")]').text.split("Einde:")[0]
            contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

    # Onsite Field -Einde:
    # Onsite Comment -take 'Einde:' as contract_end_date from the given selector

        try:
            contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvang: ")]').text.split("Einde:")[1]
            contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Hoofdcategorie:
        # Onsite Comment -None

        try:
            lot_cpvs_data = lot_cpvs()

                # Onsite Field -Hoofdcategorie:
                # Onsite Comment -None
            lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdcategorie:")]//following::dd[1]').text.split("-")[0]
            lot_cpvs_data.lot_cpv_code = re.sub("[^\d]","",lot_cpv_code)
            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass

        # Onsite Field -None
        # Onsite Comment -take award details from 'Naam en adres van de contractant' field only   for award_details ref this link : 'https://aanbestedingskalender.nl/projecten/14884501/publicaties/183830221'

        try:
            award_details_data = award_details()

                    # Onsite Field -Officiële benaming:
                    # Onsite Comment -None
            award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-9.publication > div').text.split("Naam en adres van de contractant")[1].split("Officiële benaming:")[1].split("Nationale identificatie:")[0].strip()

            try:
                award_details_data.address  = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-9.publication > div').text.split("Nationale identificatie:")[1].split("V")[0].strip()
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass

                    # Onsite Field -Aanvankelijk geraamde totale waarde van de opdracht/het perceel:
                    # Onsite Comment -split initial_estimated_value from the given selector
            try:
                initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvankelijk geraamde totale waarde van de opdracht/het perceel:")]').text.split(":")[1]
                initial_estimated_value = re.sub("[^\d\.\,]","",initial_estimated_value)
                award_details_data.initial_estimated_value =float(initial_estimated_value.replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in initial_estimated_value: {}".format(type(e).__name__))
                pass
                    # Onsite Field -Totale waarde van de opdracht/het perceel:
                    # Onsite Comment -split grossawardvaluelc from the given selector
            try:
                grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Totale waarde van de opdracht/het perceel:")]').text
                grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass

                    # Onsite Field -Datum van de sluiting van de overeenkomst:
                    # Onsite Comment -None
            try:
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Datum van de sluiting van de overeenkomst:")]//following::p[1]').text
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

#         Onsite Field -Gunningscriteria
#         Onsite Comment -None

        try:  
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Gunningscriteria")]//following::p'):
            
        # Onsite Field -Gunningscriteria
        # Onsite Comment -split tender_criteria_title  from the given selector
        
         # Onsite Field -Gunningscriteria
        # Onsite Comment -split tender_criteria_weight  from the given selector

                try:
                    if 'Kwaliteitscriterium' in single_record.text or 'Kostencriterium' in single_record.text or "Prijs" in single_record.text:
                        lot_criteria_data = lot_criteria()
                        lot_criteria_title = single_record.text
                        lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                        lot_criteria_weight = single_record.text.split('Weging:')[1].split('\n')[0]
                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)

                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                    pass
        
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://aanbestedingskalender.nl/publicaties'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#didomi-notice-agree-button > span")))
            page_main.execute_script("arguments[0].click();",click)
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.filterBlock.filterprofiles > h3')))
        except:
            pass

        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="publications"]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="publications"]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="publications"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="publications"]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
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
