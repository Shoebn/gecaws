from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_emarches_ca"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_emarches_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_emarches_ca'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
  
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box-header > div > div').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type. eg., "Travaux - Procédure Adaptée" here take only "Travaux".			 		2.Replace follwing keywords with given respective kywords ('Travaux=Works','Service=Service','Fourniture=Supply')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col1 > p:nth-child(2)').text.split("-")[0]
        if "Travaux" in notice_contract_type:
            notice_data.notice_contract_type="Works"
        elif  "Service" in notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif  "Fourniture" in notice_contract_type:
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -None
#     # Onsite Comment -1.split type_of_procedure_actual. eg., "Travaux - Procédure Adaptée" here take only "Procédure Adaptée".
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.col1 > p:nth-child(2)").text.split("-")[1].strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_emarches_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -None
#     # Onsite Comment -1.take in text.

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > a').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_no = notice_data.notice_url
        notice_no = re.findall('\d+/\d+',notice_no)[0]
        notice_data.notice_no = str(notice_no)
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
        
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#didomi-notice-agree-button > span")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(2)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tabs > ul > li')))
    except:
        pass
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#tabs > div').get_attribute("outerHTML") 
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.col2 > p > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -split est_amount after "Valeur totale du marché (hors TVA) :"

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("Valeur totale du marché (hors TVA) :")[1].split("\n")[0]
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split gross_budget_lc after "Valeur totale du marché (hors TVA) :".

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("Principale :")[1].split("-")[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    

    try:              
        # Onsite Field -None
        # Onsite Comment -1.tender_criteria_title split from "Critères d'attribution :" untill "Prix".

        tender_cri = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text
        if "Critères d'attribution :" in tender_cri:
            tender_cri1 = tender_cri.split("Critères d'attribution :")[1].split("Offre économiquement la plus avantageuse appréciée en fonction des critères énoncés ci-dessous avec leur pondération")[1].split("Date d'envoi de l'avis de publicité initial au JOUE et au BOAMP : ")[0].split('Instance chargée des procédures de recours :')[0].split("Attribution du marché")[0].strip()
            for l in tender_cri1.split('\n'):
                tender_criteria_data = tender_criteria()
                tender_criteria_title = l
                tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
                tender_criteria_weight = l
                tender_criteria_weight = re.findall('\d+% ',tender_criteria_weight)[0]
                tender_criteria_weight = (tender_criteria_weight).split("%")[0]
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
 
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        
       
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box-body-top > span').text
        

        # Onsite Field -None
        # Onsite Comment -1.split org_city. eg., here "14220 THURY HARCOURT LE HOM" take only "THURY HARCOURT LE HOM".

        try:
            org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col1 > p:nth-child(1)').text
            customer_details_data.org_city = re.sub("[^a-z A-Z]", "", org_city)
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split postal_code. eg., here "14220 THURY HARCOURT LE HOM" take only "14220".

        try:
            postal_code = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col1 > p:nth-child(1)').text
            customer_details_data.postal_code = re.sub("[^\d\.\,]", "", postal_code)
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text
            if "Nom et adresses" in org_address:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("Adresse postale:")[1].split("Code NUTS:")[0].strip()
            else:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("AVIS D'ATTRIBUTION")[1].split("Tél :")[0].split("mèl :")[0].strip()
            
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split org_email after "mèl :".

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("mèl :")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split org_website after "web :".

        try:
            customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("web :")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split org_website after "Tél :". 	2.eg., "Tél : 01 64 43 15 00 - Fax : 01 60 64 22 08" here take only "01 64 43 15 00" in org_phone.

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("Tél :")[1].split("Fax :")[0]            
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split org_website after "Fax :". 			2.eg., "Tél : 01 64 43 15 00 - Fax : 01 60 64 22 08" here take only "01 60 64 22 08" in org_fax.

        try:
            customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, 'div.html > div > div').text.split("Fax :")[1].split("\n")[0]            
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:         
        lot_number = 1
        for single_record in page_details.find_element(By.CSS_SELECTOR, '#tabs > div').text.split('\n'):
            if "Lot nº:" in single_record :
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                # Onsite Field -None
                # Onsite Comment -1.take each lot seperately. split after "LOT N°".         2.use this as reference url "https://www.e-marchespublics.com/attribution/ile-de-france/hauts-de-seine/malakoff/951021/27622".	 3.if not availabel then take local_title in lot_title.

                try:
                    lot_details_data.lot_title = single_record.split("Intitulé: ")[1].split("Lot nº:")[0].strip()
                    lot_details_data.lot_title_english = lot_details_data.lot_title
                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass
                

#             # Onsite Field -None
#             # Onsite Comment -1.lot_actual_number split after "Marché n° :"       2.use this as reference url "https://www.e-marchespublics.com/attribution/ile-de-france/hauts-de-seine/malakoff/951021/27622".

                try:
                    lot_actual_number = single_record
                    lot_details_data.lot_actual_number = re.findall('Lot nº:\d+',lot_actual_number)[0]
                except:
                    try:
                        lot_actual_number = single_record
                        lot_details_data.lot_actual_number = re.findall('Lot nº: \d+',lot_actual_number)[0]
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass
                    
            elif "Nom officiel :" in single_record :
                
                try:
                    award_details_data = award_details()
                    try:
                        award_details_data.bidder_name = single_record.split("Nom officiel : ")[1]
                    except Exception as e:
                        logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                        pass

            # Onsite Field -Adresse
            # Onsite Comment -take address from "Bezuschlagte(r) Bieter" field only

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-marchespublics.com/attribution"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#didomi-notice-agree-button > span")))
            page_main.execute_script("arguments[0].click();",click)
            time.sleep(2)
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#results > h1')))
        except:
            pass
        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="result-panel"]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result-panel"]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result-panel"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="paginate"]/div/i[3]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="result-panel"]/div'),page_check))
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
