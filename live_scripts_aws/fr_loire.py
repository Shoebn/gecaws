from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_loire"
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
SCRIPT_NAME = "fr_loire"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_loire'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
   
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.small > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take only notice_no for eg: take only 'N112IF01'

    try:
        notice_data.notice_no = tender_html_element.find_element(By.XPATH, '//div/div[2]/div[2]/div/div[2]/div/div[1]/div').text.split("|")[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.date.date-min").text
        
        if "Juin." in publish_date:
            publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
            publish_date = publish_date.replace('\n'," ")
            publish_date = publish_date.replace('June','Jun')
            publish_date = re.findall('\d+ \w+. \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        elif "Sept." in publish_date:
            publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
            publish_date = publish_date.replace('\n'," ")
            publish_date = publish_date.replace('Sept','Sep')
            publish_date = re.findall('\d+ \w+. \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        else:
            publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
            publish_date = publish_date.replace('\n'," ")
            publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -None
    # Onsite Comment -Replace following keywords with given respective keywords ('Travaux = works','Fournitures = supply','Services = Services')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie > span').text
        if "Services" in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Fournitures" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Travaux" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        lot_number=1
        url1 = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li:nth-child(1) > div > a').get_attribute("href") 
        url2=url1.split('id')[1].split('&')[0] 
        url3='https://marches.loire-atlantique.fr/index.php?page=Entreprise.PopUpDetailLots&orgAccronyme=t5y&id'+str(url2)+'&lang='
        fn.load_page(page_details1,url3,80)
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#container > div > div > div > div > div'):
            lot_details_data = lot_details()
            lot_details_data.lot_number=lot_number
            single_record.click()
            time.sleep(3)
            
            try:
                WebDriverWait(page_details1, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.modal-header')))
            except:
                pass
            
            try:
                lot_details_data.lot_actual_number = single_record.text.split(":")[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_title = single_record.text.split(":")[1]
                lot_details_data.lot_title_english =GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
            
            try:
                lot_cpvs_data = lot_cpvs()
                lot_cpv = page_details1.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::span[1]').text
                lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv)[0]
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -Catégorie :
#         # Onsite Comment -click on '+' to get the data and Replace following keywords with given respective keywords ('Travaux = works','Fournitures = supply','Services = Services')

            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        pass
    
     # Onsite Field -None 
    # Onsite Comment -click on '+' to get more data and split lot_actual_number from the given selector take only 'Lot 1','Lot 2'... only
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul > li:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#layout-entreprise').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet :
    # Onsite Comment -None
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#collapseHeading > div.panel-heading.clearfix")))
        page_details.execute_script("arguments[0].click();",click)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.panel-heading.clearfix > h1')))
    except:
        pass
    
    
    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, 'span.green.bold').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet :")]//following::span[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_summary_english
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procédure :
    # Onsite Comment -click on '+' to get type_of_procedure_actual
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procédure :")]//following::div[1]').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_loire_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        # Onsite Field -Organisme :
        # Onsite Comment -take only 'Organisme :' data

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.XPATH, '//div/div/div/div[3]/div/span[2]').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lieux-exe > span > span:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'li:nth-child(4) > div > span:nth-child(n)'):
            
        # Onsite Field -Code CPV :
        # Onsite Comment -click on '+' to get cpv_code:

            cpv_code = single_record.text
            cpv_code1 = re.findall('\d{8}',cpv_code)[0].strip()
            cpvs_data = cpvs()
            cpvs_data.cpv_code=cpv_code1
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '.picto-link a'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -'li.picto-link > span > a' use both this selector and take file_name in textform

            try:
                attachments_data.file_name = single_record.text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -'li.picto-link > span > a' use both this selector and split file_size

            try:
                file_size = single_record.text
                file_size =GoogleTranslator(source='auto', target='en').translate(file_size)
                file_size=re.search(r"\d+\.\d+\s\w+",file_size)
                attachments_data.file_size=file_size.group()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -'li.picto-link > span > a' and 'div.actions > ul > li:nth-child(2) > a' from tender_html_page  also take both this selector

            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
    urls = ['https://marches.loire-atlantique.fr/?page=Entreprise.EntrepriseAdvancedSearch&AllCons'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_resultSearch_PagerBottom_ctl2 > span > i")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div[2]'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
