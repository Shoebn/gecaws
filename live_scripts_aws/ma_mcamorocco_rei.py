from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ma_mcamorocco_rei"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ma_mcamorocco_rei"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

# Note:after opening the url click on "Appels à manifestation d'intérêt" this keyword in tender_html_element.
    
    notice_data.script_name = 'ma_mcamorocco_rei'
 
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'MAD'
    
    notice_data.main_language = 'FR'

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 5
    
    # Onsite Field -Numéro
    # Onsite Comment -None

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        if notice_no !='':
            notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#block-mca-content > article').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Date publication
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date publication")]//following::div[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} - \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Date limite
    # Onsite Comment -None
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Date limite")]//following::div[1]').text
        notice_deadline = re.findall('\d+/\d+/\d{4} - \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

# Onsite Field -Documents à télécharger
# Onsite Comment -None
# reference_url=https://www.mcamorocco.ma/fr/amilocation-de-vehicules-avec-chauffeurs-incluant-les-frais-de-carburant-et-de-peage-des-autoroutes

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.row.li-style > div > a'):
            attachments_data = attachments()
        # Onsite Field -Documents à télécharger
        # Onsite Comment -None
            attachments_data.file_name = single_record.text  
        # Onsite Field -Documents à télécharger
        # Onsite Comment -None
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass   

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'MILLENNIUM CHALLENGE ACCOUNT (MCA)-Morocco'
        customer_details_data.org_parent_id = '7586426'
        customer_details_data.org_country = 'MA'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
# reference_url=https://www.mcamorocco.ma/fr/avis-dappel-manifestation-dinteret-ami-contrats-cadres-pour-service-de-restauration

    try:              
        lot_details_data = lot_details()
    # Onsite Field -REFRENCE
    # Onsite Comment -None
        lot_details_data.lot_number = 1
        try:
            lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"REFRENCE")]//following::td[3]').text
        except:
            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > p:nth-child(4)  b > u').text.split("REFRENCE :")[1]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

    # Onsite Field -BIENS OU SERVICE
    # Onsite Comment -None
        try:
            lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"BIENS OU SERVICE")]//following::td[3]').text            
            lot_details_data.lot_title_english = GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
        except:
            lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"BIENS OU SERVICE")]//following::span[1]').text
            lot_details_data.lot_title_english = GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)

    # Onsite Field -BIENS OU SERVICE
    # Onsite Comment -None

        try:
            lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"BIENS OU SERVICE")]//following::td[3]').text
            lot_details_data.lot_description_english = GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_description)
        except:
            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"BIENS OU SERVICE")]//following::ul[1]').text
                lot_details_data.lot_description_english = GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
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
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.mcamorocco.ma/fr/appels-d-offres"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="block-mca-content"]/div/div[2]/div[1]/h2[2]/a')))
        page_main.execute_script("arguments[0].click();",clk)

        try:
            for page_no in range(1,3):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tab_content_manifestation"]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tab_content_manifestation"]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tab_content_manifestation"]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//a[@class="page-link"])[last()]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tab_content_manifestation"]/div/table/tbody/tr'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
