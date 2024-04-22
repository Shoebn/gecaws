from gec_common.gecclass import *
import time
import logging
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
SCRIPT_NAME = "be_publicproc_pp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = "be_publicproc_pp"
        
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BE'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 3

    notice_data.document_type_description = 'Planning'
    try:
        notice_data.notice_no = tender_html_element.text.split('Reference number')[1].split('\n')[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    org_name = tender_html_element.text.split('Organisation')[1].split('\n')[1].split('\n')[0]

    try:
        notice_deadline = tender_html_element.text.split('Submission deadline')[1].split('\n')[1].split('\n')[0].strip()
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.text.split('Publication date')[1].split('\n')[1].split('\n')[0].strip()
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_data.contract_type_actual = tender_html_element.text.split('Nature(s)')[1].split('\n')[1].split('\n')[0]
        if 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        if 'Supplies' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        if 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    try:
        notice_data.class_at_source = 'CPV'
        cpv_data =tender_html_element.text.split('Category (CPV code)')[1].split('\n')[1].split('\n')[0].strip()
        class_codes_at_source1 =tender_html_element.text.split('Category (CPV code)')[1].split('\n')[1].split('\n')[0].strip() 
        notice_data.class_title_at_source = class_codes_at_source1.split('(')[0]
        cpv_regex = re.findall(r'\d{8}',cpv_data)
        cpv_at_source = ''
        class_codes_at_source = ''
        for code1 in cpv_regex:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = code1
            cpv_at_source += code1
            cpv_at_source += ','
            class_codes_at_source += code1
            class_codes_at_source += ','
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass

    try:
        dispatch_date = tender_html_element.text.split('Dispatch date')[1].split('\n')[1].split('\n')[0].strip()
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    try:
        notice_data.type_of_procedure_actual = tender_html_element.text.split('Procedure')[1].split('\n')[1].split('\n')[0]
        type_of_procedure_en = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("be_publicproc_procedure.csv",type_of_procedure_en)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass   
    try:
        notice_data.notice_url = tender_html_element.get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    
    try:
        notice_data.local_description =tender_html_element.text.split('Description')[1].split('\n')[1].split('\n')[0]
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass



    try:
        url2=page_details.find_element(By.CSS_SELECTOR,'#app-init-container--router-view > div > div.app-container > div.wrap > div > div > div > div:nth-child(6) > div.col-12.col-md-4.col-lg-3.col > div > div > a:nth-child(4)').get_attribute('href')
        fn.load_page(page_details1,url2,180)
        try:
            notice_data.main_language = page_details2.find_element(By.CSS_SELECTOR,'#app-init-container--router-view > div > div.app-container > div.wrap > div > div > div > div:nth-child(6) > div.col-12.col-md-8.col-lg-9.col > div > div:nth-child(3) > div > div > div.v-card__text > div > div > div.v-data-table__wrapper > table > tbody > tr:nth-child(1) td:nth-child(3)').text
            
        except: 
            notice_data.main_language = 'EN'
    except:
        pass

    customer_details_data = customer_details()
    customer_details_data.org_country = 'BE'
    customer_details_data.org_language = notice_data.main_language
    customer_details_data.org_name = org_name
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)
    
    try:
        url3=page_details.find_element(By.CSS_SELECTOR,'#app-init-container--router-view > div > div.app-container > div.wrap > div > div > div > div:nth-child(6) > div.col-12.col-md-4.col-lg-3.col > div > div > a:nth-child(2)').get_attribute('href')
        fn.load_page(page_details3,url3,180)

        try:
            attachments_data = attachments()
            external_url = page_details3.find_element(By.CSS_SELECTOR,'#app-init-container--router-view > div > div.app-container > div.wrap > div > div > div > div:nth-child(6) > div.col-12.col-md-8.col-lg-9.col > div > div:nth-child(3) > div:nth-child(1) > div > div.container.page-header.pa-0.px-4.container--fluid > div.row.page-header--bar.flex-nowrap.align-center.page-header--bar__h2 > div:nth-child(3) > button')
            page_details1.execute_script("arguments[0].click();",external_url)
            time.sleep(10)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            attachments_data.file_name = 'Tender Documents'
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__))
            pass
    except:
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#app-init-container--router-view > div > div > div.wrap > div > div > div > div:nth-child(6) > div.col-12.col-md-8.col-lg-9.col').get_attribute("outerHTML")                     
        notice_data.notice_text += page_details1.find_element(By.XPATH,'//*[@id="app-init-container--router-view"]/div/div/div[2]/div/div/div/div[6]/div[2]/div/div[3]/div[1]/div').get_attribute("outerHTML")
    except:
        pass
    
    notice_data.identifier =  str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)  
page_details3 = Doc_Download.page_details 
page_details2 =  fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.publicprocurement.be/bda?page=1&itemsPerPage=25&sortDesc=false&includeOrganisationChildren=true&formTypes=PLANNING"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#app-init-container--router-view > div > div > div.wrap > div > div > div > div:nth-child(3) > div.col-12.col-md-8.col-lg-9.col > div > div:nth-child(n) > div > a'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#app-init-container--router-view > div > div > div.wrap > div > div > div > div:nth-child(3) > div.col-12.col-md-8.col-lg-9.col > div > div:nth-child(n) > div > a')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#app-init-container--router-view > div > div > div.wrap > div > div > div > div:nth-child(3) > div.col-12.col-md-8.col-lg-9.col > div > div:nth-child(n) > div > a')))[records]
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,' //*[@id="app-init-container--router-view"]/div/div/div[2]/div/div/div/div[3]/div[2]/div/div[26]/div[4]/button/span/i')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#app-init-container--router-view > div > div > div.wrap > div > div > div > div:nth-child(3) > div.col-12.col-md-8.col-lg-9.col > div > div:nth-child(n) > div > a'),page_check))
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
