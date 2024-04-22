from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pl_propublico_spn"
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
from selenium.webdriver.chrome.options import Options
import gec_common.OutputJSON
from gec_common import functions as fn

#Note:Open the site than click on "Ogłoszenia" this button than grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pl_propublico_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'pl_propublico_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'PLN'
   
    notice_data.main_language = 'PL'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -Signature
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Topic
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Deadline For Submission
    # Onsite Comment -Note:Grab time also  24.01.2024 10:00:00
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.replace('\n',' ').strip()
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main-content').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            
        # Onsite Field -Informacje ogólne >> Data publikacji  : 2024-01-08 15:00:37
        # Onsite Comment -Note:Splite after "Data publikacji" this keyword

        try:
            publish_date = page_details.find_element(By.CSS_SELECTOR, "div.row > div.col-md-12.col-lg-6.col-xl-5").text
            publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

         # Onsite Field -Termin otwarcia ofert
        # Onsite Comment -Note:Grab time also 2024-01-24 10:00:00
        try:
            document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Termin otwarcia ofert")]//following::div[1]').text
            document_opening_time = re.findall('\d{4}-\d+-\d+',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%Y-%m-%d').strftime('%Y-%m-%d')
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass
        
        #(Dostawy=Supply,Usługi=Service,Roboty budowlane=Works)
        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Rodzaj zamówienia")]//following::div[1]').text
            if 'Dostawy' in notice_data.contract_type_actual :
                notice_data.notice_contract_type = 'Supply'
            elif 'Usługi' in notice_data.contract_type_actual :
                notice_data.notice_contract_type = 'Service'
            elif 'Roboty budowlane' in notice_data.contract_type_actual :
                notice_data.notice_contract_type = 'Works'
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
            pass
    
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'PL'
            customer_details_data.org_language = 'PL'
            # Onsite Field -Purchaser

            customer_details_data.org_name = org_name
            
            # Onsite Comment -Note:Add also "div.card > div > div:nth-child(3)" this selector and grab the data

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#BodyLayout > div.col-md-8.col-lg-8.col-xl-9.col-12.main-content > div:nth-child(1) > div').text.split('Tel')[0].replace(customer_details_data.org_name,'').strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            # Onsite Field -Tel
            # Onsite Comment -Note:Splite after "Tel" thid keyword

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Tel.:")]').text.split('Tel.:')[1].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            # Onsite Field -Faks
            # Onsite Comment -Note:Splite after "Faks" this keyword

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faks:")]').text.split('Faks:')[1].strip()
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

            # Onsite Field -e-mail:
            # Onsite Comment -Note:Splite after "e-mail:" this keyword... Take a first value

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"e-mail:")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            # Onsite Field -Adres strony internetowej:
            # Onsite Comment -Note:Splite after "Adres strony internetowej" this keyword... Take a first value

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adres strony internetowej:")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            # Onsite Field -Informacje ogólne >> Osoba publikująca
            # Onsite Comment -Note:Splite after "Osoba publikująca" this keyword

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.row > div.col-md-12.col-lg-6.col-xl-7').text.split('Osoba publikująca:')[1].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        # Onsite Comment -Note:Click on "Dokumenty zamówienia" this tab on page_detail than grab the data
        try: 
            notice_url = page_details.find_element(By.CSS_SELECTOR, 'a#navItem_dokumentyZamowienia').get_attribute("href")                     
            fn.load_page(page_details1,notice_url,80)
            logging.info(notice_url)
            time.sleep(5)

            for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#checkable > tbody > tr'):
                attachments_data = attachments()

                try:
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in file_name: {}".format(type(e).__name__))
                    pass


                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                try:
                    file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text 
                    attachments_data.file_size  = file_size + 'KB' 
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

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
page_details1 = webdriver.Chrome(options=options)  
page_details1.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://e-propublico.pl/"] 
    for url in urls:
        fn.load_page(page_main, url, 60)
        logging.info('----------------------------------')
        logging.info(url)
        
        Ogłoszenia_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Ogłoszenia')))
        page_main.execute_script("arguments[0].click();",Ogłoszenia_click)
        time.sleep(2)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div/table/tbody/tr'),page_check))
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
