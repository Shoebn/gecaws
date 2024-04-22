from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_tjsp"
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_tjsp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_tjsp'
    notice_data.main_language = 'PT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'BRL'
    notice_data.notice_type = 4
    notice_data.procurement_method = 2

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, 'h5 > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        clk1 = tender_html_element.find_element(By.CSS_SELECTOR,"div > h6 > a").click()
        time.sleep(3)
        notice_data.notice_url=page_main.current_url
        logging.info(notice_data.notice_url)
    except:
        clk1 = WebDriverWait(tender_html_element, 20).until(EC.element_to_be_clickable((By.LINK_TEXT,'Pregão eletrônico')))
        tender_html_element.execute_script("arguments[0].click();",clk1)
        time.sleep(5) 
        notice_data.notice_url=page_main.current_url
        pass
    
    try:
        page_main.switch_to.frame(0)
    except:
        pass
    
    try:
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.sds-container.sds-margin-vertical > div > div > ul > li'):  
            attachments_data = attachments()

            try:
                file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[-1].strip()

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


            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text 
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass


            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'a').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass


            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")  
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk2 = page_main.find_element(By.CSS_SELECTOR,'section > div > div:nth-child(5) > section > ul > li:nth-child(4)').click()
        time.sleep(4)
    except:
        pass

    try:
        publish_date = page_main.find_element(By.CSS_SELECTOR, "p > span > span:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
        
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        clk3 =  page_main.find_element(By.CSS_SELECTOR,' div.sds-col-xs-12.sds-col-md-4.sds-data.sds-align-right > button').click()
        time.sleep(5) 
    except:
        pass
    
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.portal-col__wrapper').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    
    try:
        notice_deadline = page_main.find_element(By.CSS_SELECTOR, "div > span > span:nth-child(1)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div > p').text   
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)  
        
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = notice_data.notice_title
        notice_data.notice_no = re.findall('\d+/\d{4}',notice_no)[0]
    
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div > p').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO'
        customer_details_data.org_parent_id = '7785047'
        customer_details_data.org_country = 'BR'
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk4 = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' section > div > div:nth-child(1) > div > button'))).click()
        time.sleep(5) 
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
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

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tjsp.jus.br/adm/portal-servicos-frontend/portal-servicos-scl"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            iframe = page_main.find_element(By.XPATH,'//*[@id="portal-servicos-scl"]')
            page_main.switch_to.frame(iframe)
        except:
            pass

        try:
            rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.sds-container.sds-margin-vertical > div > div > div')))
            length = len(rows)
            for records in range(0,length):  
                try:
                    page_main.switch_to.frame(0)
                    iframe = page_main.find_element(By.XPATH,'//*[@id="portal-servicos-scl"]')
                    page_main.switch_to.frame(0)
                except:
                    pass
                
                tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.sds-container.sds-margin-vertical > div > div > div')))[records]
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
