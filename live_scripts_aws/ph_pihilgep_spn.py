from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ph_pihilgep_spn"
log_config.log(SCRIPT_NAME)
import re,time
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
tnotice_count = 0
SCRIPT_NAME = "ph_pihilgep_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'ph_pihilgep_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PH'
    notice_data.performance_country.append(performance_country_data)
    

    notice_data.currency = 'PHP'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.main_language = 'EN'

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if "Civil Works" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.strip()
        type_of_procedure_actual = notice_data.type_of_procedure_actual.split('(Sec')[0].lower()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/ph_philgep_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    block_content = page_details.find_element(By.CSS_SELECTOR,'#block_content').text
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice Reference Number")]//parent::label').text.split(':')[1].strip()
    except:
        try:
            notice_data.notice_no = fn.get_after(block_content,'Control Number:',15)
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    try:
        publish_date = fn.get_after(block_content,'Published Date:',25)
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ \w+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = fn.get_after(block_content,'Closing Date:',25)
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ \w+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_duration = fn.get_after(block_content,'Bid Validity Period (in Days):',4).strip() + '(in Days)'
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:
        dispatch_date = fn.get_after(block_content,'Date created:',25)
        dispatch_date = re.findall('\d+-\w+-\d{4} \d+:\d+ \w+',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d-%b-%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Line Item Details")]//following::table').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div[2]/section/div/div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        netbudgetlc = fn.get_after(block_content,'Approved Budget of the Contract:',20)
        netbudgetlc = re.sub("[^\d\.\,]", "",netbudgetlc)
        netbudgetlc = netbudgetlc.replace(',','').strip()
        notice_data.netbudgetlc = float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        category = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC")]//following::tr/td[2]').text
        notice_data.category = fn.CPV_mapping("assets/ph_pihilgep_spn_category.csv",category)[0]
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        cpv_no = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC")]//following::tr/td[2]').text
        cpv_codes = fn.CPV_mapping("assets/ph_philgeps_spn_cpv.csv",cpv_no)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
       
        try:
            customer_details_data.contact_person = fn.get_after(block_content,'Contact Person:',40).split('Created By')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'PH'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_number=1 
        for single_record in WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="block_content"]/div[4]/div[2]/table[2]/tbody/tr')))[1:]:
            lot_details_data=lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR,' td:nth-child(3)').text
            lot_details_data.lot_title_english = lot_details_data.lot_title
            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR,' td:nth-child(4)').text
                lot_details_data.lot_description_english = lot_details_data.lot_description
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
            
            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass

    try:
        Document_click = WebDriverWait(page_details, 60).until(EC.element_to_be_clickable((By.LINK_TEXT,"Preview")))
        page_details.execute_script("arguments[0].click();",Document_click)
        time.sleep(7) 
        rows = WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#facebox_div > div > div > div.panel-body > div > table > tbody > tr')))
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#facebox_div > div > div > div.panel-body > div > table > tbody > tr'):
            try:
                attachments_data = attachments()
                
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2) > a').text
                
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,' td:nth-child(2) > a').get_attribute('href')
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                if attachments_data.file_name != '':
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except:
                pass
        Document_close = WebDriverWait(page_details, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.close")))
        page_details.execute_script("arguments[0].click();",Document_close)
        time.sleep(2) 
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
   
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/section/div[2]/div/div[2]/div/div/table/tbody/tr'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://philgeps.gov.ph/Indexes/index"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,5):                                                               
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table.table.table-bordered.table-hover.text-center > tbody > tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-bordered.table-hover.text-center > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-bordered.table-hover.text-center > tbody > tr')))[records]
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
                view_more =  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.wrapper > div.content > section > div.container > div > div.tab-content > div > div > div > a")))
                page_main.execute_script("arguments[0].click();",view_more)
                logging.info("view_more")
            except:
                pass

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.wrapper > div.content > section > div > div.new-home > div.tab-content > div > div > div > div > ul > li.next > a")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table.table.table-bordered.table-hover.text-center > tbody > tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break

    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
