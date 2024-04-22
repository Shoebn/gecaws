#in this script there are two main url's.after opening the url take data after clicking this two tabs:"/html/body/section[2]/div[2]/a"

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "dz_safqatic_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "dz_safqatic_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'dz_safqatic_spn'
    notice_data.main_language = 'AR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DZ'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'DZD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'article > p').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DZ'
        customer_details_data.org_language = 'AR'
        customer_details_data.org_name = 'ministere de la poste et des Télécommunications'
        customer_details_data.org_parent_id = '7806037'

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.entete-map > p').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.items-buttons > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'p.p-petit').text.strip()
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[-1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.main-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.items-offres > div:nth-child(1) > p:nth-child(2)").text
        try:
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    


#reference_url:"https://www.safqatic.dz/ar/detail_offre.php?id=72994"	if "Extension date" is availabel then take this date as notice_deadline otherwise take "Deadline date".    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        try:
            deadline = page_details.find_element(By.CSS_SELECTOR, "div.items-offres > div:nth-child(3) > p:nth-child(2)").text
            if '-' in deadline or '/' in deadline:
                notice_deadline = deadline
            else:
                notice_deadline = page_details.find_element(By.CSS_SELECTOR, "div.items-offres > div:nth-child(2) > p:nth-child(2)").text
        except:
            notice_deadline = page_details.find_element(By.CSS_SELECTOR, "div.items-offres > div:nth-child(2) > p:nth-child(2)").text
            
        try:
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except:
            notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

#refer the "No. 22/2023" tender for lot_details    
# Onsite Field -None
# Onsite Comment -None

    try:
        lotss = tender_html_element.find_element(By.CSS_SELECTOR, 'article > p').text
        if 'Lot' in lotss:
            lotts = lotss.split("Lot")[1:]
        elif 'LOT' in lotss:
            lotts = lotss.split("LOT")[1:]
        lot_number = 1
        for single_record in lotts:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

        # Onsite Field -1.split lot_title after "Lot 01" and "Lot 02".
        # Onsite Comment -None
            lot_title = single_record
            if ':' in lot_title:
                lot_details_data.lot_title = lot_title.split(':')[1].strip()
                lot_actual_number = single_record.split(':')[0].strip()
                lot_details_data.lot_actual_number = "Lot"+' '+lot_actual_number
            elif '-' in lot_title:
                lot_details_data.lot_title = lot_title.split('-')[1].strip()
                lot_actual_number = single_record.split('-')[0].strip()
                lot_details_data.lot_actual_number = "Lot"+' '+lot_actual_number

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document'
        attachments_data.file_description = 'Tender Document'
        
        attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.items-buttons > div:nth-child(1) > a').get_attribute('href')

    # Onsite Field -None
    # Onsite Comment -1.take only file_extension.

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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.safqatic.dz/index.php","https://www.safqatic.dz/ar/index.php?type=2","https://www.safqatic.dz/ar/index.php?type=1"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
            
        all_sel = ['//*[@class="active-lien-appels-offre"][@href]','//*[@class="active-lien-avis-consult"][@href]']
        for c_sel in all_sel:
            clk = page_main.find_element(By.XPATH, c_sel).click()
            n_type = page_main.find_element(By.XPATH, c_sel).text
            time.sleep(3)
            try:
                for page_no in range(2,10):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/section[2]/div[4]'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/div')))
                    length = len(rows)
                    for records in range(3,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/div')))[records]
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
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/section[2]/div[4]'),page_check))
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
