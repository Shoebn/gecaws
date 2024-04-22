from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_emarches"
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
SCRIPT_NAME = "fr_emarches"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

#after opening the url select "Appel d'offres" and click on ""Lancer la recherche" button and take record of Tenders.

    notice_data.script_name = 'fr_emarches'
  
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'FR'
    
    notice_data.currency = 'EUR'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box-header > div > div').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type. eg., "Travaux - Procédure Adaptée" here take only "Travaux".			 		2.Replace follwing keywords with given respective kywords ('Travaux=Works','Service=Service','Fourniture=Supply')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col1 > p:nth-child(2)').text.split("-")[0].strip()
        if "Travaux" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "Service" in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Fourniture" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split type_of_procedure_actual. eg., "Travaux - Procédure Adaptée" here take only "Procédure Adaptée".
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.col1 > p:nth-child(2)").text.split("-")[1].strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_emarches_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.take in text.

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'form.d-flex > a:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take publish_date as threshold date.
#     notice_data.publish_date = 'threshold'
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "span.pink").text
        notice_deadline= re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    try:
        if "http" in tender_html_element.find_element(By.CSS_SELECTOR, 'div.box-footer > div > form > a:nth-child(2)').get_attribute('href'):
            attachments_data = attachments()
            attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box-footer > div > form > a:nth-child(2)').text
            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box-footer > div > form > a:nth-child(2)').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'form.d-flex > a:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[@id='didomi-notice-agree-button']")))
        page_details.execute_script("arguments[0].click();",click)
    except:
        pass
    
    try:
        holder= WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tabs-1"]/div/div[1]/div/div')))
    except:
        pass
    try:    
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form.d-flex > a:nth-child(1)').get_attribute("outerHTML").split('" class=')[0].split("/")[-2:]
        notice_data.notice_no="/".join(notice_no)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#tabs > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),'Description succincte:')]//following::div").text
        if notice_summary_english != "" or notice_summary_english is not None:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split dispatch_date after "Date d'envoi du présent avis " keyword.

    try:
        if "Date d'envoi du présent avis" in notice_data.notice_text:
            dispatch_date = page_details.find_element(By.CSS_SELECTOR,"div.html > div > div").text.split("Date d'envoi du présent avis")[1].strip()
            dispatch_date = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
            try:
                dispatch_date= re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
                notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                dispatch_date= re.findall('\w+ \d+, \d{4}',dispatch_date)[0]
                notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.dispatch_date)
    except:
        try:
            dispatch_date = page_details.find_element(By.XPATH,"//*[contains(text(),'Date d’envoi du présent avis:')]//following::div[1]").text
            dispatch_date= re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.dispatch_date)
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None  div.html > div > div
    # Onsite Comment -split est_amount after "Valeur totale estimée"

    try:
        est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Valeur totale estimée')]//following::div[1]").text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(' ','.').replace('.','').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:              
        cpv_code1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Code CPV principal')]//following::div").text.split(" ")[0].strip()
        cpvs_data = cpvs()
        cpvs_data.cpv_code = cpv_code1
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except:
        try:
            cpv_code2  = page_details.find_element(By.XPATH,"//*[@id='IV']/div").text.split("CPV - Objet principal : ")[1].split(".")[0].strip()
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code2
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__))
            pass
        
    try:    
        text1=page_details.find_element(By.CSS_SELECTOR, '#tabs > div').text
    except:
        pass
    
    try:
        if "Critères d'attribution" in text1:
            tender_criteria_data = tender_criteria()
        # Onsite Field -None
        # Onsite Comment -1.tender_criteria_title split after "Critères d'attribution :" or "Critère d'attribution"

            tender_criteria_title = text1.split("Critères d'attribution")[1].split("\n")[1].split("\n")[0].strip()
            tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
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
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col1 > p:nth-child(1)').text.split(" ")[1].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split postal_code. eg., here "14220 THURY HARCOURT LE HOM" take only "14220".
        
        try:
            customer_details_data.postal_code = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col1 > p:nth-child(1)').text.split(" ")[0].strip()
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -None
        # Onsite Comment -1.split org_email after "mèl :" or "Courriel:".
        try:
            if "Courriel:" in text1 or "email :" in text1:
                try:
                    customer_details_data.org_email = text1.split("Courriel:")[1].split("\n")[0].strip()
                except:
                    customer_details_data.org_email = text1.split("email :")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split org_website after "web :".

        try:
            if "web :" in text1:
                customer_details_data.org_website = text1.split("web :")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -1.split customer_nuts after "Code NUTS:"	2.refer this url "https://www.e-marchespublics.com/appel-offre/pays-de-la-loire/mayenne/laval/952195/28512".

        try:
            if "Code NUTS:" in text1:
                customer_details_data.customer_nuts = text1.split("Code NUTS: ")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_address = text1.split("Nom complet de l'acheteur : ")[1].split("Code Postal")[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try: 
        lot_number =1
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="V"]'):
            data = single_record.text.split('Description du lot')
            for single_record1 in data[1:]:
                lot_details_data = lot_details()

                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = single_record1.split('\n')[1].split("\n")[0]
        
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
                try:
                    cpvs_code = single_record1.split('Objet principal :')[1].split('.')[0].strip()
                    cpv_regex = re.compile(r'\d{8}')
                    cpvs_data = cpv_regex.findall(cpvs_code)
                    for cpv in cpvs_data:
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = cpv
                        notice_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpv_code: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
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
    urls = ["https://www.e-marchespublics.com/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[@id='didomi-notice-agree-button']")))
            page_main.execute_script("arguments[0].click();",click)
        except:
            pass
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[@id='notices-list']")))
            page_main.execute_script("arguments[0].click();",click)
        except:
            pass
        
        try:
            holder= WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="result-panel"]/div')))
        except:
            pass
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="result-panel"]/div[3]/div[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result-panel"]/div')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result-panel"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#paginate > div > i.fas.fa-angle-right")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="result-panel"]/div[3]/div[2]'),page_check))
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
