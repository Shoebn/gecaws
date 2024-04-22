from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "nl_tenderned_ca"
log_config.log(SCRIPT_NAME)
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
from webdriver_manager.chrome import ChromeDriverManager

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "nl_tenderned_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

#1) For Contract Award details : 1) go to url 
                       #2) in the Filter section click on "Publicatietype:" drop down 
                       #3) after clicking, select ( Aankondiging gegunde opdracht) option for award details
                       #4) no need to submit the result they will autometically generates the result

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'nl_tenderned_ca'
    notice_data.main_language = 'NL'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NL'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2   
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -split and take data after publish_date

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > mat-card-subtitle > div:nth-child(2)').text.split('-')[1].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.tn-h3 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -None
    # Onsite Comment -split and take only date and take time also if available

    try: 
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-subtitle > div:nth-child(2)').text.split('-')[0].strip()
        publish_date = GoogleTranslator(source='nl', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+ \d{4}',publish_date)[0]
        try:
            notice_data.publish_date = datetime.strptime(publish_date,'%b %d %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return    
    
    # Onsite Field -None
    # Onsite Comment -after clicking you will see  tabs  such as  "Details","Publicatie","Documenten","Vraag en antwoord"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.tn-link').get_attribute("href")                             
        fn.load_page(page_details,notice_data.notice_url,100)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:  
        only_num = notice_data.notice_url.split('/')[-1].strip()
    except:
        pass
    # Onsite Field -None
    # Onsite Comment -take data from all tabs ("Details","Publicatie","Documenten","Vraag en antwoord") and close take data from tender_html_page ( "//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card" )
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.tap-detail-container').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'//h3'))).text
    time.sleep(5)
        
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),"Procedure")]//following::tn-read-more[1]''').text
        type_of_procedure_actual =GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/nl_tenderned_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Type opdracht
    # Onsite Comment -split and take "Type opdracht" only  ('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),"Type opdracht")]//following::tn-read-more[1]''').text
        if "Leveringen" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Diensten" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Werken" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Referentienummer
    # Onsite Comment - click on "Details" to get the data and if notice_no is not available the take notice_no from notice_url 

    try:
        notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Referentienummer")]//following::div[1]').text
        if notice_no == "-" or notice_no =='' or notice_no ==' ':
            pass
        else:
            notice_data.notice_no = notice_no
    except:
        pass
    
    try:
        if notice_data.notice_no =='' or notice_data.notice_no == None:
            notice_data.notice_no = only_num
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
            
    # Onsite Field -Aanvang opdracht
    # Onsite Comment - click on "Details" to get the data

    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvang opdracht")]//following::div[1]').text
        tender_contract_start_date = re.findall('\d+ \w+. \d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voltooiing opdracht
    # Onsite Comment - click on "Details" to get the data

    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Voltooiing opdracht")]//following::div[1]').text
        tender_contract_end_date = re.findall('\d+ \w+. \d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass 
    try:  
        extra_cpv_clk = page_details.find_element(By.XPATH, '(//*[contains(text(),"Lees meer")])[7]').click()
        time.sleep(2)
    except:
        pass

    notice_data.class_at_source = 'CPV'        
    cpv_at_source = ''
    try:      
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdopdracht (CPV code)")]//following::div[1]').text
        for each_cpv_code in cpv_code.split('\n')[:]:

            cpv_code = re.findall('\d{8}',each_cpv_code)[0]
            cpv_at_source += cpv_code
            cpv_at_source += ','

            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)      
        notice_data.cpv_at_source = cpv_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in cpvs1: {}".format(type(e).__name__)) 
        pass
    
    try:    
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Bijkomende opdracht(-en) (CPV code)")]//following::div[1]').text
        for each_cpv_code in cpv_code.split('\n')[:]:
            cpv_code = re.findall('\d{8}',each_cpv_code)[0]
            cpv_at_source += cpv_code
            cpv_at_source += ','

            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)

        notice_data.cpv_at_source = cpv_at_source.rstrip(',')       
    except Exception as e:
        logging.info("Exception in cpvs2: {}".format(type(e).__name__)) 
        pass
  
    try:
        clk_Publicatie = page_details.find_element(By.XPATH, '//h2[contains(text(),"Publicatie")]/.').click()
        time.sleep(2)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="publicatie-eforms"]/table/tbody/tr[1]/th/span'))).text
    except:
        pass
    
    
    # Onsite Field -Beschrijving
    # Onsite Comment - click on "Publicatie" then click on dropdown "2. Procedure" to get the data 
    try:
        clk_Procedure = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Procedure")])[1]')))
        page_details.execute_script("arguments[0].click();",clk_Procedure)
        time.sleep(5)
    except:
        pass
    
    try:
        Procedure_text = WebDriverWait(page_details, 100).until(EC.presence_of_element_located((By.XPATH,'(//*[contains(text(),"Procedure")])[2]'))).text
        time.sleep(2)
    except:
        pass

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Beschrijving")])[1]//following::span[2]|//*[contains(text(),"Description")]//following::span[2]').get_attribute("innerHTML")
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Geraamde waarde exclusief btw
    # Onsite Comment -click on "Publicatie" then click on dropdown "2. Procedure" to get the data..., url ref: "https://www.tenderned.nl/aankondigingen/overzicht/322684"
    
    try:
        if Procedure_text !='':
            est_amount = page_details.find_element(By.XPATH, '(//*[contains(text(),"Geraamde waarde exclusief btw")])[1]//following::span[2]').text
            est_amount = re.sub("[^\d\.\,]", "", est_amount)
            notice_data.est_amount =float(est_amount.replace(' ','').replace(',','').strip())
            notice_data.netbudgeteuro = notice_data.est_amount 
            notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        clk_Perceel = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Perceel")])[1]|(//*[contains(text(),"Lot")])[1]')))
        page_details.execute_script("arguments[0].click();",clk_Perceel)
        time.sleep(5)
    except:
        pass
    
    try:
        Perceel_text = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'(//*[contains(text(),"Perceel")])[2]|(//*[contains(text(),"Lot")])[2]'))).text
        time.sleep(2)
    except:
        pass
            
# Onsite Field -Perceel = "information about lots"
# Onsite Comment -click on "Publicatie" than click on "Perceel", ref link "https://www.tenderned.nl/aankondigingen/overzicht/324172"
    try:
        page_text = page_details.find_element(By.XPATH, '//*[@class="header2 open"]/..').text
    except:
        pass
    
    try:
        lot_number = 1
        for single_record in page_text.split('LOT-000')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Titel
        # Onsite Comment -None
            try:
                lot_details_data.lot_title = single_record.split("Titel: ")[1].split('\n')[0].strip()
            except:
                lot_details_data.lot_title = single_record.split("Title:")[1].split('\n')[0].strip()
            # Onsite Field -Perceel
        # Onsite Comment -here take only "LOT-0001" as lot_actual_number
            try:
                lot_actual_number = single_record.split("\n")[0].strip()
                lot_details_data.lot_actual_number = "LOT-000"+lot_actual_number
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

        # Onsite Field -Beschrijving
        # Onsite Comment -take "Beschrijving" which is only in lots and after lot_title  # Beschrijving:  Description:

            try:
                lot_details_data.lot_description = single_record.split("Beschrijving:")[1].split('\n')[0].strip()
            except:
                try:
                    lot_details_data.lot_description = single_record.split("Description:")[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

        # Onsite Field -Onderverdeling land (NUTS)
        # Onsite Comment -ref url: "https://www.tenderned.nl/aankondigingen/overzicht/322684"  # 

            try:
                lot_details_data.lot_nuts = single_record.split("Onderverdeling land (NUTS):")[1].split('\n')[0].strip()
            except:
                try:
                    lot_details_data.lot_nuts = single_record.split("Country subdivision (NUTS):")[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

        # Onsite Field -Geraamde waarde exclusief btw  Geraamde waarde exclusief btw:
        # Onsite Comment -

            try:
                lot_netbudget_lc = single_record.split("Geraamde waarde exclusief btw:")[1].split('\n')[0].strip()
                lot_netbudget_lc = re.sub("[^\d\.\,]", "", lot_netbudget_lc)
                lot_details_data.lot_netbudget_lc = float(est_amount.replace(' ','').replace(',','').strip())
                lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc 
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass

         # Onsite Field -Aard van het contract
        # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322690"  Aard van het contract: Nature of the contract:

            try:
                try:
                    lot_details_data.lot_contract_type_actual = single_record.split("Aard van het contract:")[1].split('\n')[0].strip()
                except:
                    lot_details_data.lot_contract_type_actual = single_record.split("Nature of the contract:")[1].split('\n')[0].strip()

                if "Leveringen" in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = "Supply"
                elif "Diensten" in lot_details_data.lot_contract_type_actual or "Services" in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = "Service"
                elif "Werken" in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = "Works"
                else:
                    pass
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass

        # Onsite Field -Begindatum
        # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322690"  2024-04-01+02:00

            try:
                try:
                    contract_start_date = single_record.split("Begindatum:")[1].split('\n')[0].strip()
                except:
                    contract_start_date = single_record.split("Start date:")[1].split('\n')[0].strip()
                contract_start_date = re.findall('\d{4}-\d+-\d+.\d+:\d+',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%Y-%m-%d+%H:%M').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass

        # Onsite Field -Einddatum

        # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322690"     
            try:
                try:
                    contract_end_date = single_record.split("Einddatum:")[1].split('\n')[0].strip()
                except:
                    contract_end_date = single_record.split("End date:")[1].split('\n')[0].strip()
                contract_end_date = re.findall('\d{4}-\d+-\d+.\d+:\d+',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%Y-%m-%d+%H:%M').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass

        # Onsite Field -Hoeveelheid
        # Onsite Comment -None   

            try:
                lot_quantity = single_record.split("Hoeveelheid:")[1].split('\n')[0].strip()
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

        # Onsite Field -Geraamde duur >> Looptijd
        # Onsite Comment -ref urle :- "https://www.tenderned.nl/aankondigingen/overzicht/324172"  Looptijd:

            try:
                lot_details_data.contract_duration = single_record.split("Looptijd:")[1].split('\n')[0].strip()
            except:
                try:
                    lot_details_data.contract_duration = single_record.split("Duration:")[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

            try:
                # Onsite Field -Aanvullende classificatie
                try:
                    lot_cpv_at_source_str2 = ''
                    try:
                        lot_cpvs_text = single_record.split('Doel')[1].strip()
                    except:
                        lot_cpvs_text = single_record.split('Purpose')[1].strip()

                    for each_lot_cpvs in lot_cpvs_text.split('(cpv):')[1:]:
                        code = re.findall('\d{8}',each_lot_cpvs)[0]
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = code
                        lot_cpv_at_source_str2 += code
                        lot_cpv_at_source_str2 += ','
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)

                except Exception as e:
                    logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                    pass   
                lot_cpv_at_source1 = lot_cpv_at_source_str2
                lot_details_data.lot_cpv_at_source = lot_cpv_at_source1.rstrip(',')
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass

        # Onsite Field -5.1.10 Gunningscriteria
        # Onsite Comment -take data which is in "Gunningscriteria"

            try:
                try:
                    lot_criteria_text = single_record.split('Gunningscriteria')[1]
                except:
                    lot_criteria_text = single_record.split('Award criteria')[1]

                for single_record in lot_criteria_text.split('Type:')[1:]:
                    lot_criteria_data = lot_criteria()

            # Onsite Field -5.1.10 Gunningscriteria >> Naam Gewicht (punten, exact): 
            # Onsite Comment -None 
                    try:
                        if "Gewicht (punten, exact):" in single_record:
                            lot_criteria_weight = single_record.split("Gewicht (punten, exact):")[1].split('\n')[0].strip()
                        else:
                            lot_criteria_weight = single_record.split("Gewicht (percentage, exact): ")[1].split('\n')[0].strip()
                    except:
                        lot_criteria_weight = single_record.split("Weight (points, exact):")[1].split('\n')[0].strip()

                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)

                    if lot_criteria_weight !='':
                        try:
                            lot_criteria_data.lot_criteria_title = single_record.split('\n')[0].strip()
                        except:
                            lot_criteria_data.lot_criteria_title = single_record.split('\n')[0].strip()

                    if lot_criteria_data.lot_criteria_weight >= 1 and "prijs" in lot_criteria_data.lot_criteria_title.lower():
                        lot_criteria_data.lot_is_price_related = True

            # Onsite Field -5.1.10 Gunningscriteria >> Gewicht (punten, exact)
            # Onsite Comment - None

                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass


        # Onsite Field -None
        # Onsite Comment -click on "6. Resultaten" to award details.., ref url :- "https://www.tenderned.nl/aankondigingen/overzicht/324139" 
            try:
                clk_Resultaten = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Resultaten")])[1]|(//*[contains(text(),"Results")])[1]')))
                page_details.execute_script("arguments[0].click();",clk_Resultaten)
                time.sleep(5)
            except:
                pass

            try:
                Resultaten_text = page_details.find_element(By.XPATH,'(//*[contains(text(),"resultaat")])[2]/..|(//*[contains(text(),"Result")])').text
            except:
                pass

            try:
                bidder_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Officiële naam")])[2]//following::span[2]|//*[contains(text(),"Official name")]//following::span[2]').text
            except:
                pass

            try:
                try:
                    if Resultaten_text != '' and  bidder_name !='':
                        award_details_data = award_details()

                        # Onsite Field -Officiële naam
                        # Onsite Comment -None

                        award_details_data.bidder_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Officiële naam")])[2]//following::span[2]|//*[contains(text(),"Official name")]//following::span[2]').text
                        # Onsite Field -Waarde van het resultaat
                        # Onsite Comment -None
                        try:
                            netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Waarde van het resultaat")]//following::span[2]|//*[contains(text(),"Value of the result")]//following::span[2]').text
                            netawardvaluelc = re.sub("[^\d\.\,]", "", netawardvaluelc)
                            award_details_data.netawardvaluelc = float(netawardvaluelc.replace(' ',''))
                            award_details_data.netawardvalueeuro = award_details_data.netawardvalueeuro
                        except:
                            pass
                        # Onsite Field -Waarde van het resultaat
                        # Onsite Comment -None

                        # Onsite Field -Datum waarop de winnaar is gekozen  2024-01-25+01:00
                        # Onsite Comment -if "Datum waarop de winnaar is gekozen" is not available then take "Datum van sluiting van het contract:" as award_date ( '//*[contains(text(),"Datum van sluiting van het contract")]//following::span[2]')
                        try:
                            award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Datum waarop de winnaar is gekozen")]//following::span[2]|//*[contains(text(),"Date of the conclusion of the contract")]//following::span[2]').text
                            award_date = re.findall('\d{4}-\d+-\d+',award_date)[0]
                            award_details_data.award_date = datetime.strptime(award_date,'%Y-%m-%d').strftime('%Y/%m/%d')
                        except:
                            try:
                                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Datum van sluiting van het contract")]//following::span[2]|//*[contains(text(),"Date of the conclusion of the contract")]//following::span[2]').text
                                award_date = re.findall('\d{4}-\d+-\d+',award_date)[0]
                                award_details_data.award_date = datetime.strptime(award_date,'%Y-%m-%d').strftime('%Y/%m/%d')
                            except:
                                pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                except:
                    pass
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        try:
            cpv_code = page_text.split('Doel')[1].strip()
        except:
            cpv_code = page_text.split('Purpose')[1].strip()

        for each_cpv_code in cpv_code.split('(cpv):')[1:]:
            code = re.findall('\d{8}',each_cpv_code)[0]
            cpvs_data = cpvs()
            cpvs_data.cpv_code = code

            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
        pass   
    
    try:
        clk_Organisaties = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Organisaties")])[1]|(//*[contains(text(),"Organisations")])[1]')))
        page_details.execute_script("arguments[0].click();",clk_Organisaties)
        time.sleep(5)
    except:
        pass
    
    try:
        Organisaties_text = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'(//*[contains(text(),"ORG-000")])[1]'))).text
    except:
        pass
    # Onsite Field -Publicatie
    # Onsite Comment -click on "Publicatie" than click on "Organisaties", ref link "https://www.tenderned.nl/aankondigingen/overzicht/324172"

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'NL'
        customer_details_data.org_language = 'NL'
    # Onsite Field -Officiële naam
    # Onsite Comment -None
    
        customer_details_data.org_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Officiële naam")])[1]//following::span[2]|(//*[contains(text(),"Official name")])[1]//following::span[2]').text
        
    # Onsite Field -Postadres
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postadres")]//following::span[2]|//*[contains(text(),"Postal address")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Stad
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Stad")]//following::span[2]|//*[contains(text(),"Town")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

            
    # Onsite Field -E-mail
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail")]//following::span[2]|//*[contains(text(),"Email")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contactpunt
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contactpunt")]//following::span[2]|//*[contains(text(),"Contact point")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telefoon
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon")]//following::span[2]|//*[contains(text(),"Telephone")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        # Onsite Field -Fax:
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Postcode
        # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Internetadres
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internetadres")]//following::span[2]|//*[contains(text(),"Internet address")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Activiteit van de aanbestedende dienst: 
        
        try:
            customer_details_data.customer_main_activity  = page_details.find_element(By.XPATH, '//*[contains(text(),"Activiteit van de aanbestedende ")]//following::td[1]|//*[contains(text(),"Activity of the contracting authority")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity : {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    # Onsite Field -Publicatie
    # Onsite Comment -click on "Publicatie" and click on " Download PDF " to get attachment

    try:              
        attachments_data = attachments()

        attachments_data.file_name = 'Tender Documents'


    # Onsite Field -Publicatie
    # Onsite Comment -click on "Publicatie" and click on " Download PDF " to get attachment 

        attachments_data.external_url = "https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties/"+str(only_num)+"/pdf"


        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk_Informatie_over = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Informatie over een aankondiging")])[1]')))
        page_details.execute_script("arguments[0].click();",clk_Informatie_over)
        time.sleep(5)
    except:
        pass
    
    try:
        Informatie_over_text = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'(//*[contains(text(),"Informatie over een aankondiging")])[2]'))).text
    except:
        pass
    
    try: 
        dispatch = page_details.find_element(By.XPATH, '//*[contains(text(),"Verzenddatum van de aankondiging")]/../..').text
        try:
            dispatch_date1 = re.findall('\d{4}-\d+-\d+',dispatch)[0]
            dispatch_date2 = re.findall('\d+:\d+',dispatch)[0]
            dispatch_date3 = dispatch_date1+' '+dispatch_date2
            notice_data.dispatch_date = datetime.strptime(dispatch_date3,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        except:
            dispatch_date1 = re.findall('\d{4}-\d+-\d+',dispatch)[0]
            dispatch_date2 = re.findall('\d+:\d+:\d+',dispatch)[0]
            dispatch_date3 = dispatch_date1+' '+dispatch_date2
            notice_data.dispatch_date = datetime.strptime(dispatch_date3,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-detail/span/mat-tab-group').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        clk_Documenten = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Documenten")])[1]')))
        page_details.execute_script("arguments[0].click();",clk_Documenten)
        time.sleep(5)
    except:
        pass
    
    try:
        Documenten_text = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'(//*[contains(text()," Download alle documenten ")])[1]'))).text
    except:
        pass
    
    try:              
        if Documenten_text !='':
            attachments_data = attachments()

        # Onsite Field -Documenten
        # Onsite Comment -you have to go "Documenten" tab for more attachment attachments   
            attachments_data.file_name = 'Tender Documents'

        # Onsite Field -Documenten
        # Onsite Comment -click on "Documenten" and click on "  Download alle documenten  " to get all attachment 

            attachments_data.external_url = "https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties/"+str(only_num)+"/documenten/zip"

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-detail/span/mat-tab-group').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
page_details = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenderned.nl/aankondigingen/overzicht"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk1 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/tn-root/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer/div/tn-aankondiging-filter/div[2]/div[1]/tn-publicatie-type-selector/tn-form-input-multiple-select/div/mat-form-field/div/div[1]/div/mat-select/div/div[2]')))
        page_main.execute_script("arguments[0].click();",clk1)
        time.sleep(2)
        
        clk3 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div[2]/div/div/div/mat-option[5]/span')))
        page_main.execute_script("arguments[0].click();",clk3)
        time.sleep(2)

        try:
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))[records]
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
