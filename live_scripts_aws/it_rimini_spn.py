from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_rimini_spn"
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
SCRIPT_NAME = "it_rimini_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_rimini_spn'
    
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Titolo :
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.split("Titolo :")[1]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avviso per :
    # Onsite Comment -split the data after "Avviso per :", Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','Forniture = Supply')
    
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text.split("Avviso per :")[1].strip()
        if 'Lavori' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_data.contract_type_actual: 
            notice_data.notice_contract_type = 'Supply'  
        elif 'Servizi' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service' 
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione :
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data scadenza :
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Avvisi pubblici in corso'

    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.column.content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -None
     # Onsite Field -Visualizza scheda
    # Onsite Comment -if notice_no is not available in "Riferimento procedura :" field then pass notice_no from notice_url
    
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(7)').text.split("Riferimento procedura :")[1]
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no = re.findall('\w+\d{5}',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Stazione appaltante :
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(1)').text.split("Stazione appaltante : ")[1]
        
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        # Onsite Field -RUP :
        # Onsite Comment -split the data after "RUP :" field

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section.first-detail-section > div:nth-child(3)').text.split("RUP :")[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(6) > div > ul > li'):
        # Onsite Field -Documentazione
        # Onsite Comment -None

        
        # Onsite Field -Documentazione
        # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00044&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"

            external_url = single_record.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')
            if "javascript:;" in external_url:
                pass
            else:
                attachments_data = attachments()
                attachments_data.external_url = external_url            
            try:
                attachments_data.file_name = single_record.text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.column.content > div > div:nth-child(7) ul  ul'):
            attachments_data = attachments()
        # Onsite Field -Comunicazioni della stazione appaltante
        # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00071&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"

            try:
                attachments_data.file_name = single_record.text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Comunicazioni della stazione appaltante
        # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00071&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
# Onsite Field -Altri documenti
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > ul > li form'):
        # Onsite Field -Documenti
        # Onsite Comment -in detail_page click on "Altri documenti"  (selector : "div > div:nth-child(5) > div:nth-child(8)  ul li a") for attachments  and split the data from "Altri documenti",    ref_url_of_detail_page1 = "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/viewAltriDocumenti.action&currentFrame=7&codice=A00071&ext=&_csrf=AUQFAS01VQ9YI4Q8IEXFDQKLTUDYONKL"
            doc_url = single_record.get_attribute('action')
            fn.load_page(page_details2,doc_url,100)

            for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'a.bkg'):
                attachments_data = attachments()
            # Onsite Field -Comunicazioni della stazione appaltante
            # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00071&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"

                try:
                    attachments_data.file_name = single_record.text
                except Exception as e:
                    logging.info("Exception in file_name: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Comunicazioni della stazione appaltante
            # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00071&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass  
            
# Onsite Field -Comunicazioni della stazione appaltante
# Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00071&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"
    
    try:
        attach_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div:nth-child(8) > ul > li > a"))).get_attribute("href")                     
        logging.info(attach_url)
        fn.load_page(page_details1,attach_url,100)
    except:
        pass
    
    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div > ul > li form'):
        # Onsite Field -Documenti
        # Onsite Comment -in detail_page click on "Altri documenti"  (selector : "div > div:nth-child(5) > div:nth-child(8)  ul li a") for attachments  and split the data from "Altri documenti",    ref_url_of_detail_page1 = "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/viewAltriDocumenti.action&currentFrame=7&codice=A00071&ext=&_csrf=AUQFAS01VQ9YI4Q8IEXFDQKLTUDYONKL"
            doc_url = single_record.get_attribute('action')
            fn.load_page(page_details3,doc_url,100)

            for single_record in page_details3.find_elements(By.CSS_SELECTOR, 'a.bkg'):
                attachments_data = attachments()
            # Onsite Field -Comunicazioni della stazione appaltante
            # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00071&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"

                try:
                    attachments_data.file_name = single_record.text
                except Exception as e:
                    logging.info("Exception in file_name: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Comunicazioni della stazione appaltante
            # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00071&_csrf=H4VOXDJD0170LZ59AA1DQ78EEJYX02L7"

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
page_details2 = fn.init_chrome_driver(arguments)
page_details3 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?_csrf=3MZ0CPGOMB62CF6QLQ4W5CODC6ICQOD"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[7]/div/div[1]/div[2]/form/div')))
            length = len(rows)
            for records in range(2,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[7]/div/div[1]/div[2]/form/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details2.quit()
    page_details3.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
