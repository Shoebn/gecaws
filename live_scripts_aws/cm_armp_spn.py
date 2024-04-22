from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cm_armp_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cm_armp_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global es_amount1
    notice_data = tender()

    notice_data.script_name = 'cm_armp_spn'

    notice_data.main_language = 'FR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CM'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'XAF'
    
       
    try:
        type1 = tender_html_element.find_element(By.XPATH, '//*[contains(text(),"Type:")]//following::div[1]').text
        notice_data.document_type_description = type1
    except:
        pass
    
    if 'Call for Tenders' in type1:
        notice_data.procurement_method = 2
    if 'National Call for Tenders' in type1:
        notice_data.procurement_method = 0
    else:
        notice_data.procurement_method = 2
    if 'Call for Expression of Interest' in type1:
        notice_data.notice_type = 5
    else:
        notice_data.notice_type = 4
        
    
    try:  
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-table-row.armp-color-green > div:nth-child(2)').text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:  
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, ' div.col-md-5.col-12.d-table > div:nth-child(2) > div:nth-child(2)').text
        notice_deadline2 = tender_html_element.find_element(By.CSS_SELECTOR, ' div.col-md-5.col-12.d-table > div:nth-child(3) > div:nth-child(2)').text
        notice_deadline = notice_deadline1+' '+notice_deadline2
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, ' div.col-md-6.col-12.d-table.px-0 > div:nth-child(4) > div.d-table-cell.armp-color-red').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except:
        pass
    
    try: 
        attachments_data = attachments()
        
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-5.col-12.d-table > div:nth-child(4) > div:nth-child(1) > a').get_attribute("href")

        attachments_data.file_name ='Dowload'


        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div.col-md-10.col-12 > div.text-left.line-clamp > strong').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
   
    org_name = tender_html_element.find_element(By.CSS_SELECTOR,' div.col-md-6.col-12.d-table.px-0 > div:nth-child(1) > div:nth-child(2)').text
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.btn.btn-sm.armp-bg-black.armp-color-white.w-40.w-md-100.mt-md-2.avis-link.text-center').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
        
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="the_wrappper_new"]/div[2]').get_attribute("outerHTML")
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
        
    try:
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        customer_details_data.org_phone = '(+237) 222 201 803 ,(+237) 222 200 008 ,(+237) 222 200 009 ,(+237) 222 206 043'
        customer_details_data.org_email = 'infos@armp.cm'
        customer_details_data.org_country = 'CM'
        customer_details_data.org_language = 'FR'
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[@id="the_wrappper_new"]/div[2]/div[5]/div[2]/div[3]').text
        except:
            pass
        

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:
        notice_data.notice_no = re.findall('\d+',notice_data.notice_url)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
        
    try:
        contract_Duration1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée Validité des Offres")]//following::p[1]').text
        contract_Duration = re.findall("\d+",contract_Duration1)[0]
        notice_data.contract_duration = contract_Duration+ ' days'
    except Exception as e:
        logging.info("Exception in contract_Duration: {}".format(type(e).__name__))
        pass
    
       
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ['https://armp.cm/']
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tout_les_avis"]/li/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="tout_les_avis"]/li/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="tout_les_avis"]/li/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="my_pagination"]/nav/ul/li[15]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tout_les_avis"]/li/div'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
