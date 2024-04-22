from gec_common.gecclass import *
import logging
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
from selenium.webdriver.chrome.options import Options
import gec_common.Doc_Download_ingate

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "nl_tenderned_pp"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

#1) For Contract Award details : 1) go to url 
                       #2) in the Filter section click on "Publicatietype:" drop down 
                       #3) after clicking, select "Vooraankondiging" option for pp
                       #4) no need to submit the result they will autometically generates the result

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'nl_tenderned_pp'
    
    notice_data.main_language = 'NL'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 3
    
    notice_data.class_at_source = 'CPV'         
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.tn-h3 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
        
    # Onsite Comment -split and take only date and take time also if available  29 jan. 2024 
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div > mat-card-subtitle > div:nth-child(2)').text.split('-')[0].strip()
        publish_date = GoogleTranslator(source='nl', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%b %d %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div > mat-card-subtitle > div:nth-child(2)').text.split('-')[0].strip()
            publish_date = GoogleTranslator(source='nl', target='en').translate(publish_date)
            publish_date = re.findall('\w+ \d+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return  

     # Onsite Comment -split and take data after publish_date
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div > mat-card-subtitle > div:nth-child(2)').text.replace(publish_date,'').strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Sluitingsdatum  May 2, 2024, 2:00 PM
    # Onsite Comment -if available the take notice_deadline otherwise take deadline of one year from publish_date and take time also if available 

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(1) > div:nth-child(2)").text
        notice_deadline = re.findall('\w+ \d+ \d{4}, \d+:\d+ [PMAMpmam]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y, %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(1) > div:nth-child(2)").text
            notice_deadline = GoogleTranslator(source='nl', target='en').translate(notice_deadline)
            notice_deadline = re.findall('\w+ \d+ \d{4}, \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d %Y, %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(1) > div:nth-child(2)").text
                notice_deadline = GoogleTranslator(source='nl', target='en').translate(notice_deadline)
                notice_deadline = re.findall('\w+ \d+, \d{4}, \d+:\d+',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline, "%B %d, %Y, %I:%M %p").strftime('%Y/%m/%d %H:%M:%S')
            except:
                try:
                    notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(1) > div:nth-child(2)").text
                    notice_deadline = GoogleTranslator(source='nl', target='en').translate(notice_deadline)
                    notice_deadline = re.findall('\w+ \d+, \d{4}, \d+:\d+',notice_deadline)[0]
                    notice_data.notice_deadline = datetime.strptime(notice_deadline, "%B %d, %Y, %I:%M").strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                    pass
    
    # Onsite Field -Procedure
    # Onsite Comment -split and take "Procedure" only
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, " mat-card-content > div:nth-child(2)").text.split('Procedure')[1].strip()
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/nl_tenderned_pp_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type opdracht
    # Onsite Comment -split and take "Type opdracht" only 
    # Onsite Comment -split and take "Type opdracht" only and  Replace following keywords with given respective keywords 
    #('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, ' mat-card-content > div:nth-child(3)').text.split('Type opdracht\n')[1].split('\n')[0].strip()
        if 'Werken' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Diensten' in notice_data.contract_type_actual: 
            notice_data.notice_contract_type = 'Service'
        elif 'Leveringen' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -after clicking you will see  tabs  such as  "Details","Publicatie","Documenten","Vraag en antwoord"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.tn-link').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep(5)
        
        # Onsite Comment -take data from all tabs ("Details","Publicatie","Documenten","Vraag en antwoord") and close take data from tender_html_page ( "//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card" )
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').get_attribute("outerHTML")                     
        except Exception as e:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')  
        
        # Onsite Field -Referentienummer  https://www.tenderned.nl/aankondigingen/overzicht/323085
        # Onsite Comment - click on "Details" to get the data and if notice_no is not available the take notice_no from notice_url 
        try:
            notice_data.notice_no = notice_data.notice_url.split('/')[-1].strip()
        except:
            try:
                notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Referentienummer")]//following::div[1]').text
                if notice_data.notice_no == '-':
                    notice_data.notice_no = notice_data.notice_url.split('overzicht/')[1].strip()
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Hoofdopdracht (CPV code)
        # Onsite Comment - click on "Details" to get the data
        try:
            try:
                cpv_at_source_str1 = ''
                cpv_at_source_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdopdracht (CPV code)")]//following::div[1]').text
                cpv_regex = re.compile(r'\d{8}')
                cpv_at_source = cpv_regex.findall(cpv_at_source_code)
                for code in cpv_at_source:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = code
                    cpv_at_source_str1 += code
                    cpv_at_source_str1 += ','
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in cpv_at_source_1: {}".format(type(e).__name__))
                pass

            # Onsite Field -Bijkomende opdracht(-en) (CPV code)
            # Onsite Comment - click on "Details" to get the data
            try:
                cpv_at_source_str2 = ''
                cpv_at_source_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Bijkomende opdracht(-en) (CPV code)")]//following::div[1]').text
                cpv_regex = re.compile(r'\d{8}')
                cpv_at_source = cpv_regex.findall(cpv_at_source_code)
                for code in cpv_at_source:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = code
                    cpv_at_source_str2 += code
                    cpv_at_source_str2 += ','
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in cpv_at_source_2: {}".format(type(e).__name__))
                pass
            cpv_at_source1 = cpv_at_source_str1 + cpv_at_source_str2
            notice_data.cpv_at_source = cpv_at_source1.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
            pass
        
# As of now tender_contract_start_date and tender_contract_end_date not available in both fields Aanvang opdracht and Voltooiing opdracht on side so we can't grap the dates
        
        # Onsite Field -Aanvang opdracht
        # Onsite Comment - click on "Details" to get the data

#         try:
#             notice_data.tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvang opdracht")]//following::div[1]').text
#         except Exception as e:
#             logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
#             pass

        # Onsite Field -Voltooiing opdracht
        # Onsite Comment - click on "Details" to get the data

#         try:
#             notice_data.tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Voltooiing opdracht")]//following::div[1]').text
#         except Exception as e:
#             logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
#             pass
        
        try:
            Publicatie_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Publicatie")]')))
            page_details.execute_script("arguments[0].click();",Publicatie_click)
            time.sleep(4) 
            
            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').get_attribute("outerHTML")                     
            except Exception as e:
                logging.info("Exception in notice_text_2: {}".format(type(e).__name__))
                pass
            
            try:              
                attachments_data = attachments()
                attachments_data.file_name = 'Tender Documents'

                external_url = page_details.find_element(By.XPATH,'//*[@id="mat-tab-content-0-1"]/div/tn-aankondiging-publicatie-tab//div/button').click()
                time.sleep(3)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                
                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except:
                    pass
                    
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
                pass

            try:
                Procedure_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Procedure")]')))
                page_details.execute_script("arguments[0].click();",Procedure_click)
                time.sleep(4) 

                 # Onsite Field -Beschrijving
                # Onsite Comment - click on "Publicatie" then click on dropdown "2. Procedure" to get the data 
                try:
                    notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschrijving")]//following::span[2]').text
                    notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                except Exception as e:
                    logging.info("Exception in local_description: {}".format(type(e).__name__))
                    pass
                
                # Onsite Field -Geraamde waarde exclusief btw
                # Onsite Comment -click on "Publicatie" then click on dropdown "2. Procedure" to get the data..., url ref: "https://www.tenderned.nl/aankondigingen/overzicht/324104"

                try:
                    est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text
                    est_amount = re.sub("[^\d\.\,]", "", est_amount) 
                    notice_data.est_amount = float(est_amount.replace(',','.').replace('.','').strip())
                    notice_data.netbudgetlc = notice_data.est_amount
                    notice_data.netbudgeteuro = notice_data.est_amount
                except Exception as e:
                    logging.info("Exception in est_amount: {}".format(type(e).__name__))
                    pass
            except:
                pass
            
            try: 
                try:
                    Perceel_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Perceel")])')))
                    page_details.execute_script("arguments[0].click();",Perceel_click)
                    time.sleep(5)
                except:
                    Deel_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Deel")])[2]')))
                    page_details.execute_script("arguments[0].click();",Deel_click)
                    time.sleep(5)
                lot_title = page_details.find_element(By.XPATH, '(//*[contains(text(),"Titel")]//following::span[2])[2]').text
                if lot_title != '':
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = 1 

                    # Onsite Field -Titel
                    lot_details_data.lot_title = page_details.find_element(By.XPATH, '(//*[contains(text(),"Titel")]//following::span[2])[2]').text
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                    # Onsite Field -Beschrijving
                    # Onsite Comment -take "Beschrijving" which is only in lots and after lot_title 
                    try:
                        lot_details_data.lot_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Beschrijving")]//following::span[2])[2]').text
                        lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                    except Exception as e:
                        logging.info("Exception in lot_description: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Deel
                    # Onsite Comment -here take only "PAR-0000" as lot_actual_number

                    # Onsite Field -Perceel
                    # Onsite Comment -here take only "LOT-0001" as lot_actual_number
                    try:
                        lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '(//*[contains(text(),"Deel")]//following::span[2])[3]').text
                    except:
                        try:
                            lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Perceel")]//following::span[3]').text
                        except Exception as e:
                            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                            pass

                    # Onsite Field -Onderverdeling land (NUTS)
                    # Onsite Comment -take only if its in lot 
                    try:
                        lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '(//*[contains(text(),"Onderverdeling land (NUTS)")]//following::td[1])[2]').text
                    except Exception as e:
                        logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Geraamde waarde exclusief btw 
                    try:
                        lot_netbudget_lc = page_details.find_element(By.XPATH, '(//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2])[2]').text
                        lot_netbudget_lc = re.sub("[^\d\.\,]", "", lot_netbudget_lc) 
                        lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(',','.').replace('.','').strip())
                        lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
                    except Exception as e:
                        logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Begindatum 2024-06-03+02:00
                    # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322411"
                    try:
                        contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Begindatum")]//following::span[2]').text
                        contract_start_date = re.findall('\d{4}-\d+-\d+[+]\d+:\d+',contract_start_date)[0]
                        lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%Y-%m-%d+%H:%M').strftime('%Y/%m/%d %H:%M:%S')
                    except Exception as e:
                        logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Einddatum 2026-11-01+01:00
                    # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322411"
                    try:
                        contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Einddatum")]//following::span[2]').text
                        contract_end_date = re.findall('\d{4}-\d+-\d+[+]\d+:\d+',contract_end_date)[0]
                        lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%Y-%m-%d+%H:%M').strftime('%Y/%m/%d %H:%M:%S')
                    except Exception as e:
                        logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Hoeveelheid
                    try:
                        lot_quantity = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoeveelheid")]//following::span[2]').text
                        lot_quantity = re.sub("[^\d\.\,]", "", lot_quantity) 
                        lot_details_data.lot_quantity = float(lot_quantity.replace(',','.').replace('.','').strip())
                    except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Geraamde duur >> Looptijd
                    # Onsite Comment -ref urle :- "https://www.tenderned.nl/aankondigingen/overzicht/324046"
                    try:
                        lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd")]//following::td[1]').text
                    except Exception as e:
                        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                        pass

                     # Onsite Field -Aard van het contract
                    # Onsite Comment -Replace following keywords with given respective keywords 
                    #('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')ref url "https://www.tenderned.nl/aankondigingen/overzicht/322411"
                    try:
                        lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '(//*[contains(text(),"Aard van het contract")]//following::span[2])[2]').text
                        if 'Werken' in lot_details_data.lot_contract_type_actual:
                            lot_details_data.contract_type = 'Works'
                        elif 'Diensten' in lot_details_data.lot_contract_type_actual: 
                            lot_details_data.contract_type = 'Service'
                        elif 'Leveringen' in lot_details_data.lot_contract_type_actual:
                            lot_details_data.contract_type = 'Supply'
                    except Exception as e:
                        logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                        pass

                    try:
                        # Onsite Field -Belangrijkste classificatie
                        try:
                            lot_cpv_at_source_str1 = ''
                            lot_cpv_at_source = page_details.find_element(By.XPATH, '(//*[contains(text(),"Belangrijkste classificatie")]//following::td[1])[2]').text
                            cpv_regex = re.compile(r'\d{8}')
                            cpv_at_source = cpv_regex.findall(lot_cpv_at_source)
                            for code in cpv_at_source:
                                lot_cpvs_data = lot_cpvs()
                                lot_cpvs_data.lot_cpv_code = code
                                lot_cpv_at_source_str1 += code
                                lot_cpv_at_source_str1 += ','
                                lot_cpvs_data.lot_cpvs_cleanup()
                                lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        except Exception as e:
                            logging.info("Exception in lot_cpv_at_source_1: {}".format(type(e).__name__))
                            pass

                        # Onsite Field -Aanvullende classificatie
                        try:
                            lot_cpv_at_source_str2 = ''
                            lot_cpv_at_source = page_details.find_element(By.XPATH, '(//*[contains(text(),"Aanvullende classificatie")]//following::td[1])[2]').text
                            cpv_regex = re.compile(r'\d{8}')
                            cpv_at_source = cpv_regex.findall(lot_cpv_at_source)
                            for code in cpv_at_source:
                                lot_cpvs_data = lot_cpvs()
                                lot_cpvs_data.lot_cpv_code = code
                                lot_cpv_at_source_str2 += code
                                lot_cpv_at_source_str2 += ','
                                lot_cpvs_data.lot_cpvs_cleanup()
                                lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        except Exception as e:
                            logging.info("Exception in lot_cpv_at_source_2: {}".format(type(e).__name__))
                            pass   
                        lot_cpv_at_source1 = lot_cpv_at_source_str1 + lot_cpv_at_source_str2
                        lot_details_data.lot_cpv_at_source = lot_cpv_at_source1.rstrip(',')
                        notice_data.cpv_at_source = notice_data.cpv_at_source+','+lot_details_data.lot_cpv_at_source
                    except Exception as e:
                        logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_criteria_title = []
                        for single_record in page_details.find_elements(By.XPATH, '(//*[contains(text(),"Gunningscriteria")]//following::tr)//*[contains(text(),"Naam")]//following::td[1]'):
                                criteria_title = single_record.text
                                lot_criteria_title.append(criteria_title)

                        lot_criteria_weight = []
                        for single_record in page_details.find_elements(By.XPATH, '(//*[contains(text(),"Gunningscriteria")]//following::tr)//*[contains(text(),"Vaste waarde (totaal)")]//following::td[1]'):
                            criteria_weight = single_record.text
                            lot_criteria_weight.append(criteria_weight)

                        for title_data,weight_data in zip(lot_criteria_title,lot_criteria_weight):
                            lot_criteria_data = lot_criteria()
                            lot_criteria_data.lot_criteria_title = title_data

                            lot_criteria_weight1 = weight_data
                            lot_criteria_weight1 = re.sub("[^\d\.\,]", "", lot_criteria_weight1)
                            lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight1.replace(',','').replace('.','').strip())

                            lot_criteria_data.lot_criteria_cleanup()
                            lot_details_data.lot_criteria.append(lot_criteria_data)
                    except Exception as e:
                        logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                        pass
                    
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__))
                pass
            
# Onsite Field -Publicatie
# Onsite Comment -click on "Publicatie" than click on "Organisaties", ref link "https://www.tenderned.nl/aankondigingen/overzicht/324104"
            
            try: 
                Organisaties_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Organisaties")]')))
                page_details.execute_script("arguments[0].click();",Organisaties_click)
                time.sleep(4) 
                
                customer_details_data = customer_details()
                customer_details_data.org_country = 'NL'
                customer_details_data.org_language = 'NL'

                # Onsite Field -Officiële naam
                customer_details_data.org_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Officiële naam")])[1]//following::span[2]|(//*[contains(text(),"Official name")])[1]//following::span[2]').text

                # Onsite Field -Postadres
                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postadres")]//following::span[2]|//*[contains(text(),"Postal address")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Stad
                try:
                    customer_details_data.org_city =page_details.find_element(By.XPATH, '//*[contains(text(),"Stad")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in org_city: {}".format(type(e).__name__))
                    pass

                 # Onsite Field -Contactpunt
                try:
                    customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contactpunt")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                # Onsite Field -E-mail
                try:
                    customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Telefoon
                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Fax:
                try:
                    customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_fax: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Postcode
                try:
                    customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Internetadres
                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internetadres")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Activiteit van de aanbestedende dienst: 
                try:
                    customer_details_data.customer_main_activity  = page_details.find_element(By.XPATH, '//*[contains(text(),"Activiteit van de aanbestedende dienst")]//following::td[1]').text
                except Exception as e:
                    logging.info("Exception in customer_main_activity : {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass
        except:
            pass
#************************************************************************************************************************** 
        try:
            Documenten_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Documenten")]')))
            page_details.execute_script("arguments[0].click();",Documenten_click)
            time.sleep(4) 
            
            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').get_attribute("outerHTML")                     
            except Exception as e:
                logging.info("Exception in notice_text_2: {}".format(type(e).__name__))
                pass
            
            try:              
                attachments_data = attachments()
                attachments_data.file_name = 'Tender Documents'

                external_url = page_details.find_element(By.XPATH,'//*[@id="mat-tab-content-0-2"]/div/tn-aankondiging-documenten-tab/div//div/button').click()
                time.sleep(3)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                
                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except:
                    pass
                
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
                pass
        except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url     
       
    
#As of now, I don't have found lot_criteria data on side so we can't grap the data

# Onsite Field -3. Deel = "information about lots"  or "Perceel = "information about lots""  
# Onsite Comment -click on "Publicatie" than click on "3. Deel", ref link "https://www.tenderned.nl/aankondigingen/overzicht/324104"
   
#         # Onsite Field -5.1.10 Gunningscriteria
#         # Onsite Comment -take data which is in "Gunningscriteria"

#             try:
#                 for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
#                     lot_criteria_data = lot_criteria()
        
                    # Onsite Field -5.1.10 Gunningscriteria >> Naam
#                     lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '(//*[contains(text(),"Gunningscriteria")]//following::tr)//*[contains(text(),"Naam")]//following::td[1]').text

#             # Onsite Field -5.1.10 Gunningscriteria >> Gewicht (punten, exact)
#             # Onsite Comment - None

#                     lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Gewicht (punten, exact)")]//following::span[2]').text

#                     lot_criteria_data.lot_criteria_cleanup()
#                     lot_details_data.lot_criteria.append(lot_criteria_data)
#             except Exception as e:
#                 logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
#                 pass
#     except Exception as e:
#         logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
#         pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details =Doc_Download.page_details
page_details.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenderned.nl/aankondigingen/overzicht"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
    
        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-select-0"]/div/div[2]')))
        page_main.execute_script("arguments[0].click();",next_page)
        
#         next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-option-1"]/mat-pseudo-checkbox')))
#         page_main.execute_script("arguments[0].click();",next_page)
        time.sleep(10)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                  
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
