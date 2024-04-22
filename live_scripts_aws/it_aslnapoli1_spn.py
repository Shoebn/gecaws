from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_aslnapoli1_spn"
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
SCRIPT_NAME = "it_aslnapoli1_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_aslnapoli1_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    notice_data.document_type_description = 'Avvisi e bandi di gara'
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data di pubblicazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,100)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    # Onsite Field -CIG
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div').text
    except:
        try:
            fst_num = notice_data.notice_url.split('_')[3]
            second_num = notice_data.notice_url.split('_')[4]
            notice_data.notice_no = fst_num+'_'+second_num
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
  
    # Onsite Field -Oggetto
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.review36').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    # Onsite Field -Procedura di scelta del contraente:
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),"Procedura di scelta del contraente:")]''').text.split('-')[1].strip()
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_aslnapoli1_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data di scadenza:
    # Onsite Comment -None

    try:
        notice_deadline = page_details.find_element(By.XPATH, '''//*[contains(text(),"Data di scadenza:")]//following::strong[1]''').text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo dell'appalto:
    # Onsite Comment -None

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '''//*[contains(text(),"Importo dell'appalto:")]|//*[contains(text(),"Totale importo dell'appalto:")]''').text.split(':')[1].strip()
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        notice_data.netbudgetlc = float(grossbudgetlc.replace('.','').replace(',','.').strip())
        notice_data.netbudgeteuro = notice_data.netbudgetlc
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedura relativa:
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Procedura relativa: ")]//following::a[1]').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Ufficio:
# Onsite Comment -(ref url 'https://aslnapoli1centro.portaleamministrazionetrasparente.it/index.php?id_oggetto=13&id_cat=0&id_doc=2551')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        # Onsite Field -Ufficio:
        # Onsite Comment -None
        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio:")]//parent::a[1]').text
        except:
            customer_details_data.org_name = "ASL Naples 1 Centre"

        # Onsite Field -RUP:
        # Onsite Comment -None
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP:")]//parent::a[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Indirizzo:
        # Onsite Comment -click on 'Ufficio:' (div.campoOggetto114 > a) to get the data

        try:
            notice_url1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio:")]//parent::a[1]').get_attribute('href')
            fn.load_page(page_details1,notice_url1,100)
            logging.info(notice_url1)
        except:
            pass
        
        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#partecentrale > div.container.container-nav-1 > div > div').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Indirizzo:")]').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.customer_main_activity = page_details1.find_element(By.XPATH, '''//*[contains(text(),'Struttura organizzativa di appartenenza:')]//following::a[1]''').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telefono:
        # Onsite Comment -click on 'Ufficio:' (div.campoOggetto114 > a) to get the data

        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Telefono:")]').text.split('Telefono:')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        # Onsite Field -Email certificate:
        # Onsite Comment -click on 'Ufficio:' (div.campoOggetto114 > a) to get the data

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email certificate:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Allegati
# Onsite Comment -(ref url 'https://aslnapoli1centro.portaleamministrazionetrasparente.it/archivio11_bandi-gare-e-contratti_0_1185126_957_1.html')

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48'):
            attachments_data = attachments()
        # Onsite Field -Allegato
        # Onsite Comment -split file_type from the given selector

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('-')[-1].split(')')[0].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegato
        # Onsite Comment -take file_name in textform

            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegato
        # Onsite Comment -split  file_size from given selector

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('-')[-2].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegato
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
# Onsite Comment -ref url 'https://aslnapoli1centro.portaleamministrazionetrasparente.it/archivio11_bandi-gare-e-contratti_0_1197900_957_1.html'

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"CIG:")]/..'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            # Onsite Field -Esiti relativi
        # Onsite Comment -click on "div.campoOggetto114 > a" to get lot_title 

            
            lot_url = single_record.find_element(By.CSS_SELECTOR, 'div > div > ul > li > div > a').get_attribute('href')
            fn.load_page(page_details2,lot_url,100)
            
            lot_details_data.lot_title = page_details2.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div > a').text
            try:
                notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#partecentrale > div.container.container-nav-1 > div > div').get_attribute("outerHTML")                     
            except:
                pass
        # Onsite Field -CIG:
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div.campoOggetto114 > a').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            # Onsite Field -Importo dell'appalto
            # Onsite Comment -split "Importo dell'appalto"

            try:
                lot_grossbudget_lc = single_record.text.split('€')[1].split('\n')[0].strip()
                lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                lot_netbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
                lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass 

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_url3 = page_details2.find_element(By.CSS_SELECTOR, 'div.campoOggetto185 > a').get_attribute('href')
        fn.load_page(page_details3,notice_url3,100)
        logging.info(notice_url1)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details3.find_element(By.CSS_SELECTOR, '#partecentrale > div.container.container-nav-1 > div > div').get_attribute("outerHTML")                     
    except:
        pass
    
    # Onsite Field -Allegati
    # Onsite Comment -click on "div.campoOggetto185 > a" from page_details1 to get attachment 

    try:              
        attachments_data = attachments()
        
        attachments_data.file_name = page_details3.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > a').text.split('.')[0].strip()

        try:
            attachments_data.file_description = page_details3.find_element(By.CSS_SELECTOR, 'div.campoOggetto48').text
        except Exception as e:
            logging.info("Exception in file_description: ", str(type(e)))
            pass

        # Onsite Field -Allegati
        # Onsite Comment -None

        try:
            attachments_data.file_type = page_details3.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > span').text.split('-')[-1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        # Onsite Field -Allegati
        # Onsite Comment -None

        try:
            attachments_data.file_size = page_details3.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > span').text.split('-')[-2].strip()
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass

        attachments_data.external_url = page_details3.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
            
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    th = date.today() - timedelta(2)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://aslnapoli1centro.portaleamministrazionetrasparente.it/pagina957_avvisi-e-bandi.html','https://aslnapoli1centro.portaleamministrazionetrasparente.it/pagina956_delibera-a-contrarre.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'>successiva')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr[2]'),page_check))
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
    page_details2.quit()
    page_details3.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
