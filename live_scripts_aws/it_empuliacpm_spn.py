
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_empuliacpm_spn"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_empuliacpm_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_empuliacpm_spn'
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'IT'
    
    notice_data.notice_type = 4
    
    # Onsite Comment -Descrizione

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: ", str(type(e)))
        pass
    
    # Onsite Field -None 30/01/2024 10:00
    # Onsite Comment -Scadenza  #NOTE- take publish_date threshold.

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline= re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: ", str(type(e)))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
       
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
    
    # Onsite Comment -Dettaglio

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) >a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
         # Onsite Field -also take notice_no from notice url   
        # Onsite Comment -split the data from "open bracket"(" till "close bracket")"

        try:
            notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#template_doc > thead > tr > th > h1').text.split('(')[1].split(')')[0].strip()
            if notice_data.notice_no == None:
                notice_data.notice_no = notice_data.notice_url.split('&bando=')[1].split('&')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'th > h1').text.split('(')[0]
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="ctl00_m_g_09b3ec71_d49c_480f_a5b4_c03b883f9e7b_dgList"]/tbody/tr"

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#template_doc > tbody ').get_attribute('outerHTML')
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            
            
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'

        # Onsite Comment -Ente Appaltante

            customer_details_data.org_name = org_name

        # Onsite Comment -Incaricato

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Incaricato:')]//following::td[1]").text
            except Exception as e:
                logging.info("Exception in contact_person: ", str(type(e)))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: ", str(type(e))) 
            pass
        
        # Onsite Field -to download zip file use "#DownloadAllegati" #NOTE- zip file is not present in each tender
        # Onsite Comment -ref url - "http://www.empulia.it/tno-a/empulia/Empulia/SitePages/New_Dettaglio%20Consultazione.aspx?getdettaglio=yes&bando=358108&tipobando=Consultazione%20Preliminare%20di%20Mercato&RicQ=NO&VisQ=SI&tipoDoc=BANDO_CONSULTAZIONE_PORTALE&xslt=XSLT_BANDO_CONSULTAZIONE_PORTALE&scadenzaBando=2024-01-29T10:00:00"

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(6) > td > table > tbody > tr')[1:]:
                attachments_data = attachments()
                
            # Onsite Comment -DESCRIZIONE

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, '#Allegato_V_N').click()
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
            
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        notice_data.notice_url = url

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = Doc_Download.page_details 
page_details.maximize_window() 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Elenco%20consultazioni%20preliminari%20di%20mercato%20new.aspx?expired=0&type=All'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_m_g_09b3ec71_d49c_480f_a5b4_c03b883f9e7b_dgList"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_m_g_09b3ec71_d49c_480f_a5b4_c03b883f9e7b_dgList"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_m_g_09b3ec71_d49c_480f_a5b4_c03b883f9e7b_dgList"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.LINK_TEXT,str(page_no)))).click()
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_m_g_09b3ec71_d49c_480f_a5b4_c03b883f9e7b_dgList"]/tbody/tr'),page_check))
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
