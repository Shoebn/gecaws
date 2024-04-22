from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ua_zakupkiprom_pp"
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
import gec_common.Doc_Download_ingate as Doc_Download


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 20000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "ua_zakupkiprom_pp"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.main_language = 'UA'
    notice_data.currency = 'UAH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 3
    
    notice_data.procurement_method = 2
    notice_data.script_name = "ua_zakupkiprom_pp"
    
    notice_data.procurement_method = 2
        
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h3.qa_title_item ').text
        if len(local_title) >=5 :
            notice_data.local_title = local_title
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        else:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass   
    
    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.zkb-list__price-value.qa_price > b').text
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace('.','').replace(',','').strip())
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    notice_data.document_type_description = "Procurement plans"

        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.zkb-list__heading.qa_title_link').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Basic Information
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, ' div.zkb-layout > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        publish_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Дата публікації:")]//following::div[1]''').text
        publish_date1 = re.findall('\d{4}-\d+-\d+',notice_data.notice_url)[0]
        publish_date3 = re.findall('\d+:\d+',publish_date)[0]
        publish_date4 = publish_date1+" "+publish_date3
        notice_data.publish_date = datetime.strptime(publish_date4,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date1 = re.findall('\d{4}-\d+-\d+',notice_data.notice_url)[0]
            notice_data.publish_date = datetime.strptime(publish_date1,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ідентифікатор плану закупівлі:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.tender_quantity = page_details.find_element(By.XPATH, '(//*[contains(text(),"Кількість")])[1]//following::td[2]').text
    except Exception as e:
        logging.info("Exception in tender_quantity: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Ідентифікатор закупівлі:")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'p.h-mb-10.h-break-word'):
            local_description += single_record.text
            local_description += ' '
        notice_data.local_description = local_description.rstrip(' ')
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description[:4500]) 
    except:
        pass

     
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Назва:")])[1]//following::span[1]').text

        try:
            org_website = page_details.find_element(By.XPATH, ' //*[contains(text(),"Веб сайт:")]//following::span[1]').text
            if "Не вказано" in org_website:
                pass
            else:
                customer_details_data.org_website = org_website
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, ' //*[contains(text(),"Адреса:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        
        customer_details_data.org_country = 'UA'
        customer_details_data.org_language = 'UA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        class_title_at_source = page_details.find_element(By.XPATH,' //*[contains(text(),"Код ДК 021:2015:")]//following::span[1]').text
        notice_data.class_title_at_source =re.split("\d+-\d+ ", class_title_at_source)[1]
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.class_codes_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Код ДК 021:2015:")]//following::span[1]').text.split(' ')[0].strip()
    except Exception as e:
        logging.info("Exception in class_codes_at_source: {}".format(type(e).__name__))
        pass
    
    notice_data.class_at_source = 'CPV'
    
    try:
        cpv_code = page_details.find_element(By.XPATH, ' //*[contains(text(),"Код ДК 021:2015:")]//following::span[1]').text
        cpvs_data = cpvs()
        cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:
        cpv_at_source = ''
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Код ДК 021:2015:")]//following::span[1]').text
        cpv_at_source += re.findall('\d{8}',cpv_code)[0]
        cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass

    try:  
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr.zkb-table-list__row.zkb-files.qa_file_list'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' div.zkb-files__name').text.split(".")[0].strip()

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' div.zkb-files__name > a').get_attribute('href')
            
            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except:
                pass
            
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' div.zkb-files__name').text.split(".")[-1].strip()
            except:
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://zakupivli.pro/gov/plans'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,500):#20
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/main/div/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    if notice_count == 50:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/main/div/ul/li'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
        except:
            logging.info('No new record')
            break
            
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
