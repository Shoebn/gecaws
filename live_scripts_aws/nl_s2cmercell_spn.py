from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "nl_s2cmercell_spn"
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
SCRIPT_NAME = "nl_s2cmercell_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'nl_s2cmercell_spn'
    
    # Onsite Field -None
    # Onsite Comment -there are multiple language included in tenders , you have to translate this site in English language
    notice_data.main_language = 'EN'
    
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NL'
    notice_data.performance_country.append(performance_country_data)
    
    
    notice_data.procurement_method = 2
    
    
    notice_data.notice_type = 4
    
    notice_data.currency = 'EUR'
    # Onsite Field -None
    # Onsite Comment -None
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.padding--right-10> span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
   
    # Onsite Field -None
    # Onsite Comment -inspect url fro detail page , url ref = "https://s2c.mercell.com/today/44215"
    
    try:
        notice_data.document_type_description = "Published tenders"
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        clk= WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div.ng-star-inserted > a > span'))).click()
        time.sleep(5)
    except:
        pass
        
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.nxcard__header.ng-star-inserted > div.nxcard__header-title > div > span')))
    except:
        pass
        
    # Onsite Field -Tender number
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender number")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publication date
    # Onsite Comment -None
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publication date")]//following::font[1]').text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publication date")]//following::div[1]').text
            publish_date1 = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            publish_date2 = re.findall('\d+:\d+',publish_date)[0]
            publish_date = publish_date1+" "+publish_date2
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -Procedure
    # Onsite Comment -split the following data from this field

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(5) > div.nxcard__body-cell.break-word.col-xs-6.col-md-8 > div').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/nl_s2cmercell_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of contract
    # Onsite Comment -split the following data from this field,  Replace following keywords with given respective keywords ('supplies = Supply ' , 'services = Services ' , 'works = Works')

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::div[1]').text
        if 'service' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Service'
        elif 'works' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Works'
        elif 'supply' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Supply'
        elif 'consultancy' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Consultancy'
        elif 'non consultancy' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Non consultancy'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::nx1-read-more-less[1]').text 
        notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        if len(notice_summary_english) > 1:
            notice_data.notice_summary_english = notice_summary_english
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::nx1-read-more-less[1]').text 
        if len(local_description) > 1:
            notice_data.local_description = local_description
        else:
            pass
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#nx1-published-tender-details > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:              
        customer_details_data = customer_details()
        
    # Onsite Field -None
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.margin--left-15> div> div').text
    
    # Onsite Field -Contact person
    # Onsite Comment -ref url : "https://s2c.mercell.com/today/44614"

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact person")]//following::a[2]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Contact person
    # Onsite Comment -ref url : "https://s2c.mercell.com/today/44614"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact person")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Contact person
    # Onsite Comment -ref url : "https://s2c.mercell.com/today/44614"

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact person")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'NL'
        customer_details_data.org_language = 'EN'
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -url ref: "https://s2c.mercell.com/today/41040"
    
    try:  
        lot_number = 1          
        for lot_record in page_details.find_elements(By.CSS_SELECTOR, '.nxcard__header-title'):
            
            if 'lot' in lot_record.text.lower():
                lot_details_data = lot_details()
                lot_details_data.lot_number =  lot_number
                # Onsite Field -None
                # Onsite Comment -url ref: "https://s2c.mercell.com/today/41040"
                lot_details_data.lot_number = lot_no
                lot_details_data.lot_title = ' '.join(lot_record.text.split(' ')[3:])
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                lot_details_data.contract_type = notice_data.notice_contract_type
            
                # Onsite Field -None
                # Onsite Comment -take only ' Lot 1' in lot_actual_number and  take only ' Lot 2' in lot_actual_number .........       ,url ref: "https://s2c.mercell.com/today/41040"

                try:
                    lot_details_data.lot_actual_number = lot_record.text.split('Lot ')[1].split('\n')[0]
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

    try:  
        #  EXPORT TENDER  button
        attachments_data = attachments()
        attachments_data.file_type = 'zip'
        attachments_data.file_name = page_details.find_element(By.XPATH, '//header/div[2]/button[1]').text
        
        external_url = page_details.find_element(By.XPATH, '//header/div[2]/button[1]')
        page_details.execute_script("arguments[0].click();",external_url)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:  
        attachments_data = attachments()
        attachments_data.file_type = 'pdf'
        
        attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#nx1-published-tender-details__nx1-scrollbar__nx1-published-tender-additional-information__nx1-published-tender-publication__name-label').text
        
        external_url = page_details.find_element(By.CSS_SELECTOR, '#nx1-published-tender-details__nx1-scrollbar__nx1-published-tender-additional-information__nx1-published-tender-publication__download-button')
        page_details.execute_script("arguments[0].click();",external_url)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk1 = page_details.find_element(By.XPATH,'//*[@id="nx1-published-tender-details__nx1-aside__nx1-published-tender-details-navigation__planning__nx1-side-navigation-node__nx-1-published-tender-details-nx-1-aside-nx-1-published-tender-details-navigation-planning-link"]').click()
        time.sleep(3)
    except:
        pass

    try:
        notice_deadline = page_details.find_element(By.XPATH, '(//*[contains(text(),"Deadline for submission of offers")])[1]//following::span[1]').text
        notice_deadline1 = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_deadline2 = re.findall('\d+:\d+',notice_deadline)[0]
        notice_deadline = notice_deadline1+" "+notice_deadline2
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://s2c.mercell.com/today"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="nx1-public-content-wrapper__nx1-published-tenders__nx1-published-tender"]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="nx1-public-content-wrapper__nx1-published-tenders__nx1-published-tender"]')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="nx1-public-content-wrapper__nx1-published-tenders__nx1-published-tender"]')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR ,"#nx1-public-content-wrapper__nx1-published-tenders__nx1-pagination__next-page-button")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="nx1-public-content-wrapper__nx1-published-tenders__nx1-published-tender"]'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
