from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_samdaily"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
import os
import csv
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.support.ui import Select
import gec_common.web_application_properties as application_properties
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 200000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "us_samdaily"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()

    
    notice_data.main_language = 'EN'

    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    
    notice_type = tender_html_element['Type']
    if 'Sources Sought' in notice_type or 'Combined Synopsis/Solicitation' in notice_type or 'Special Notice' in notice_type or 'Solicitation' in notice_type or 'Presolicitation' in notice_type or 'Sale of Surplus Property' in notice_type:
        notice_data.notice_type = 4
        notice_data.script_name = 'us_samdaily_spn'
    elif 'Award Notice' in notice_type:
        notice_data.notice_type = 7
        notice_data.script_name = 'us_samdaily_ca'
    elif 'Justification' in notice_type or 'Fair Opportunity / Limited Sources Justification' in notice_type or 'Justification and Approval (J&A)' in notice_type or 'Modification/Amendment/Cancel' in notice_type:
        notice_data.notice_type = 16
        notice_data.script_name = 'us_samdaily_amd'
                   
    try:
        performance = tender_html_element['PopCountry']
        if performance != "":
            performance_country_data = performance_country()
            p_country = fn.procedure_mapping("assets/us_samdaily_spn_countrycode.CSV",performance)
            if p_country is None:
                performance_country_data.performance_country = 'US'
            else:
                performance_country_data.performance_country = p_country
            notice_data.performance_country.append(performance_country_data)
        
        else:
            performance_country_data = performance_country()
            performance_country_data.performance_country = 'US'
            notice_data.performance_country.append(performance_country_data)
    except:
        pass
        


    try:
        published_date = tender_html_element['PostedDate']
        published_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',published_date)[0]
        notice_data.publish_date= datetime.strptime(published_date,'%Y-%m-%d %H:%M:%S').strftime("%Y/%m/%d %H:%M:%S")
        logging.info(notice_data.publish_date)
    except:
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.document_type_description = tender_html_element['Type']
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        deadline = tender_html_element['ResponseDeadLine']
        try:
            notice_deadline = re.findall('\d{4}-\d+-\d+T+\d+:\d+:\d+',deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%dT%H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_deadline = re.findall('\d{4}-\d+-\d+',deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element['Title']
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        notice_data.additional_tender_url = tender_html_element['AdditionalInfoLink']
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try: 
        notice_data.local_description = tender_html_element['Description']
        notice_data.notice_summary_english=GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.additional_tender_url =  tender_html_element['AdditionalInfoLink']
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element['Department/Ind.Agency']
        try:
            org_country = tender_html_element['CountryCode']
            org_country = fn.procedure_mapping("assets/us_samdaily_spn_countrycode.CSV", org_country )
            customer_details_data.org_country = org_country
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = tender_html_element['PrimaryContactFullname']  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_email = tender_html_element['PrimaryContactEmail']   
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass 
        
        
        try:
            customer_details_data.org_phone = tender_html_element['PrimaryContactPhone']   
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass 
        
        
        try:
            customer_details_data.org_fax = tender_html_element['PrimaryContactFax']          
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.postal_code = tender_html_element['PopZip']  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_city = tender_html_element['PopCity']          
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_state = tender_html_element['PopState']          
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_address = tender_html_element['Office']          
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
                         
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element['Department/Ind.Agency']
        try:
            org_country = tender_html_element['CountryCode']
            org_country = fn.procedure_mapping("assets/us_samdaily_spn_countrycode.CSV", org_country )
            customer_details_data.org_country = org_country
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = tender_html_element['SecondaryContactFullname']  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_email = tender_html_element['SecondaryContactEmail']   
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass 
        
        
        try:
            customer_details_data.org_phone = tender_html_element['SecondaryContactPhone']   
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass 
        
        
        try:
            customer_details_data.org_fax = tender_html_element['SecondaryContactFax']          
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.postal_code = tender_html_element['PopZip']  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_city = tender_html_element['PopCity']          
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_state = tender_html_element['PopState']          
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_address = tender_html_element['Office']          
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'US'
        if customer_details_data.contact_person != '':
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_url = tender_html_element['Link']
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += tender_html_element
    except:
        pass
        
    try:
        fn.load_page(page_details,notice_data.notice_url,180)
     
        try:
            page_details_clk = WebDriverWait(page_details, 160).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="sds-dialog-0"]/layout-splash-modal/div[4]/div[2]/div/button' )))
            page_details.execute_script("arguments[0].click();",page_details_clk)
            time.sleep(5)
        except:
            pass
        
        try:
            notice_data.notice_text += WebDriverWait(page_details, 160).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.usa-width-three-fourths.br-double-after.ng-star-inserted'))).get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
    
        try: 
            attachments_scroll = page_details.find_element(By.CSS_SELECTOR,'#opp-view-attachments-section-title')
            page_details.execute_script("arguments[0].scrollIntoView(true);", attachments_scroll)
            time.sleep(2)
            additional_tender_url = ''
            for single_record in WebDriverWait(page_details, 50).until(EC.presence_of_all_elements_located((By.XPATH, '//*[contains(text(),"Attachments")]//following::table[1]/tbody[1]/tr'))):
    
            # Onsite Field -Documentazione
            # Onsite Comment -None 
                additional_tender_probabitlity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a > span').get_attribute('innerHTML')
                if '(opens in new window)' in additional_tender_probabitlity:
                    additional_tender_url += single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href') + ','
                else:
                    attachments_data = attachments()
            # Onsite Field -Documentazione
            # Onsite Comment -split the file type , for ex . " DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx" here split only "docx", ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"
    
                    try:
                        file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
                        if 'pdf' in file_type:
                            attachments_data.file_type = 'pdf'
                        elif 'zip' in file_type:
                            attachments_data.file_type = 'zip'
                        elif 'docx' in file_type:
                            attachments_data.file_type = 'docx'
                        elif 'xls' in file_type:
                            attachments_data.file_type = 'xls'
                        elif 'xlsx' in file_type or 'XLSX' in file_type:
                            attachments_data.file_type = 'xlsx'
                        elif 'doc' in file_type:
                            attachments_data.file_type = 'doc'
                        else:
                            pass
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass
    
                # Onsite Field -Documentazione
                # Onsite Comment -split only file_name for ex."Disciplinare di gara:  DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx", here split only "Disciplinare di gara",     split the data before " :(colon) "    url ref : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"
    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
    
                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
    
                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            notice_data.additional_tender_url = additional_tender_url.rstrip(',')
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass
        
    
    if notice_data.notice_type == 7:
        try:
            notice_no = tender_html_element['AwardNumber']
            if notice_no == '':
                notice_data.notice_no = notice_data.notice_url.split('opp/')[1].split('/view')[0].strip()
            else:
                notice_data.notice_no = notice_no
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.related_tender_id = tender_html_element['Sol#']
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        
        try:  
            lot_number = 1
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
            award_details_data = award_details()

            award_details_data.bidder_name = tender_html_element['Awardee']  

            award_date = tender_html_element['AwardDate']
            award_date = re.findall('\d{4}-\d+-\d+',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%Y-%m-%d').strftime('%Y/%m/%d')

            award_details_data.grossawardvaluelc = float(tender_html_element['Award$'])

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

            if lot_details_data.award_details !=[]:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass


    else:
        try:
            notice_no = tender_html_element['Sol#']
            if notice_no == '':
                notice_data.notice_no = notice_data.notice_url.split('opp/')[1].split('/view')[0].strip()
            else:
                notice_data.notice_no = notice_no
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) + str(notice_data.publish_date)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')

arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost'] 
page_details = fn.init_chrome_driver(arguments) 
tmp_dwn_dir = application_properties.TMP_DIR#.replace('/',"\\")  #for windows uncomment --> .replace('/',"\\")
experimental_options = {"prefs": {"download.default_directory": tmp_dwn_dir}}
page_main = fn.init_chrome_driver(arguments=[], experimental_options = experimental_options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    url = 'https://sam.gov/data-services/Contract%20Opportunities/datagov?privacy=Public%27'
    logging.info(url)
    logging.info('----------------------------------')
    fn.load_page(page_main, url,80)

    #below code for latest csv download 
    clk = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="sds-dialog-0"]/layout-splash-modal/div[4]/div[2]/div/button')))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(5)

    clk = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#primary-content > div.usa-width-one-whole.data-service-content-div > div:nth-child(3) > div.usa-width-five-sixths > div > a' )))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(10)

    accept_scroll = page_main.find_element(By.CSS_SELECTOR,'#signing > div')
    page_main.execute_script("arguments[0].scrollIntoView(true);", accept_scroll)
    time.sleep(20)
    
    clk = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#sds-dialog-1 > terms-of-use-modal > div.sds-dialog-section--centered.margin-top-2 > button:nth-child(2)' )))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(220)
    with open(application_properties.TMP_DIR+"/ContractOpportunitiesFullCSV.csv", 'r', encoding="windows-1252") as f:
        lines = f.readlines()  # Skip the first two rows
        dict_reader = csv.DictReader(lines)
        ContractOpportunities_csv = list(dict_reader)
        
    for tender_html_element in ContractOpportunities_csv:
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break

        if notice_count == 50:
            output_json_file.copyFinalJSONToServer(output_json_folder)
            output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
            notice_count = 0

        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
            break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
    os.remove(application_properties.TMP_DIR+"/ContractOpportunitiesFullCSV.csv")
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()  
    output_json_file.copyFinalJSONToServer(output_json_folder)
