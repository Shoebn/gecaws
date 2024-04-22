from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_salute_spn"
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
import re
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_salute_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_salute_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    
    if url==urls[0]:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.titolo').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Data pubblicazione:
        # Onsite Comment -None

        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "p:nth-child(3)").text
            publish_date= GoogleTranslator(source='auto', target='en').translate(publish_date)
            try:
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')    
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        logging.info(notice_data.publish_date)  

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        # Onsite Field -Data scadenza
        # Onsite Comment -None

        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "p:nth-child(4)").text
            notice_deadline= GoogleTranslator(source='auto', target='en').translate(notice_deadline)
            try:
                notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]                
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S') 
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        # Onsite Field -None
        # Onsite Comment -None

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'p.titolo > a').get_attribute("href")                     
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url

        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[-1]
        except:
            pass


        try:
            WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Chiudi'))).click()
        except:
            pass

        # Onsite Field -None
        # Onsite Comment -None
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-content > div:nth-child(2)').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        try:
            notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content ').text.split('Consulta il')[0]
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except :
            try:
                notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content p').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except:
                pass
            
        try:
            email =  page_details.find_element(By.CSS_SELECTOR, "div.testo p a").text
        except:
            pass
    # Onsite Field -ul.no-border-left.span4 > li:nth-child(1) > a   ---  Biblioteca del Ministero
    # Onsite Comment -None

        try:    
            notice_url = page_details.find_element(By.CSS_SELECTOR, '#doc-navigation > div > ul.no-border-left.span4 > li:nth-child(1) > a').get_attribute("href")
            fn.load_page(page_details1,notice_url,80)
            notice_text = page_details1.find_element(By.CSS_SELECTOR,'#foglia > div > div.portlet-content').text


            customer_details_data = customer_details()
            # Onsite Field -Ufficio
            # Onsite Comment -None

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(2)').text.split('Ufficio: ')[1].strip()

            # Onsite Field -click on ---  ref url - "  Biblioteca del Ministero"  ul.no-border-left.span4 > li:nth-child(1) > a
            # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details1.find_element(By.XPATH, "//*[contains(text(),'Contatti')]//following::p[8]").text.split(':')[1]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
            # Onsite Field -click on ---  ref url - "  Biblioteca del Ministero"  ul.no-border-left.span4 > li:nth-child(1) > a
            # Onsite Comment -None

            try:
                customer_details_data.org_email = email
            except:
                customer_details_data.org_email = page_details1.find_element(By.XPATH, "//*[contains(text(),'E-mail')]//following::a[1]").text


            # Onsite Field -click on ---  ref url - "  Biblioteca del Ministero"  ul.no-border-left.span4 > li:nth-child(1) > a
            # Onsite Comment -just take the phone number

            try:
                customer_details_data.org_phone = notice_text.split('Telefono')[1].split('\n')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            customer_details_data.org_language = 'IT'
            customer_details_data.org_country = 'IT'
            customer_details_data.org_parent_id = 7359961
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

    # Onsite Field -Documentazione
    # Onsite Comment -None

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.section > ul > li'):
                attachments_data = attachments()
                    # Onsite Field -Documentazione
                    # Onsite Comment -dont take email  take "Documentazione > Bando" and "Consulta il

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'p > a').get_attribute('href')

                # Onsite Field -do not take extensions or size just grab title
                # Onsite Comment -None

                try:
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'p > a').text
                except Exception as e:
                    logging.info("Exception in file_name: {}".format(type(e).__name__))
                    pass

                # Onsite Field -just take file size
                # Onsite Comment -None

                try:
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'p.download-options').text.split('(')[1].split(',')[1].split(')')[0].strip()
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass


                # Onsite Field -just take file typesss
                # Onsite Comment -None

                try:
                    file_type = single_record.find_element(By.CSS_SELECTOR, 'p.download-options').text
                    if 'pdf' in file_type.lower():
                        attachments_data.file_type = 'pdf'
                    elif 'zip' in file_type.lower():
                        attachments_data.file_type = 'zip'
                    elif 'docx' in file_type.lower():
                        attachments_data.file_type = 'docx'
                    elif 'xlsx' in file_type.lower():
                        attachments_data.file_type = 'xlsx'
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    else:
        
        try:
            notice_data.local_title = tender_html_element.text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass


        try:
            notice_data.notice_url = tender_html_element.get_attribute("href")   
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-content > div:nth-child(2)').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
        notice_text=WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main-content"]'))).text

        # Onsite Field -Data pubblicazione:
        # Onsite Comment -None

        try:
            publish_date = notice_text.split('Data di pubblicazione:')[1].split('\n')[0]
            publish_date= GoogleTranslator(source='auto', target='en').translate(publish_date)
            try:
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')    
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        logging.info(notice_data.publish_date)  

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

    #     # Onsite Field -Data scadenza
    #     # Onsite Comment -None

        try:
            notice_deadline = notice_text.split('Data di scadenza: ')[1].split('\n')[0]
            notice_deadline= GoogleTranslator(source='auto', target='en').translate(notice_deadline)
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

    #     # Onsite Field -None
    #     # Onsite Comment -None


        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[-1]
        except:
            pass


        try:              
            customer_details_data = customer_details()
        # Onsite Field -Ufficio
        # Onsite Comment -split data from "Ufficio" till "Data pubblicazione:"

            
            customer_details_data.org_name = notice_text.split('Ente / Ufficio:')[1].split('\n')[0]



            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div> div > ul:nth-child(15) > li > a').text
            except:
                try:
                    customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content > p > a').text
                except:
                    try:
                        customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div> p:nth-child(7) > a').text
                    except:
                        pass



        # Onsite Field -click on ---  ref url - "  Biblioteca del Ministero"  ul.no-border-left.span4 > li:nth-child(1) > a
        # Onsite Comment -None
            customer_details_data.org_language = 'IT'
            customer_details_data.org_country = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass  

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#doc-pubblicazioni > ul > li > p'):
                attachments_data = attachments()
            # Onsite Field -Documentazione
            # Onsite Comment -dont take email  take "Documentazione > Bando" and "Consulta il
            
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

            # Onsite Field -do not take extensions or size just grab title
            # Onsite Comment -None

                attachments_data.file_name = single_record.text.split('(')[0]
            # Onsite Field -just take file size which is after the data 
            # Onsite Comment -None

                try:
                    attachments_data.file_size = single_record.text.split(',')[1].split(')')[0].strip()
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass


    #         # Onsite Field -just take file typesss
    #         # Onsite Comment -None

                try:
                    attachments_data.file_type = single_record.text.split('(')[1].split(',')[0].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
    
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
page_details1 = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.salute.gov.it/portale/documentazione/p6_2_7.jsp?lingua=italiano&concorsi.page=0",
           "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_1.jsp?lingua=italiano&btnCerca="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        if url==urls[0]:
            try:
                WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Chiudi'))).click()
            except:
                pass

            try:
                for page_no in range(2,40):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="page-content"]/div[2]/div[2]/div/div[1]/ul/li'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-content"]/div[2]/div[2]/div/div[1]/ul/li')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-content"]/div[2]/div[2]/div/div[1]/ul/li')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
    
                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="page-content"]/div[3]/div[2]/div/div[1]/ul/li'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            except:
                logging.info('No new record')
                break
        else:
            try:
                for page_no in range(2,40):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'dt a'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'dt a')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'dt a')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'dt a'),page_check))
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
    
