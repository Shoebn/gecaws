from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "by_zakupki_spn"
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
SCRIPT_NAME = "by_zakupki_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'by_zakupki_spn'
    notice_data.main_language = 'RU'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RU'
    notice_data.performance_country.append(performance_country_data)
    notice_data.procurement_method = 2
    notice_data.currency = 'BYN'
    notice_data.notice_url = "https://zakupki.butb.by/auctions/viewinvitation.html"
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('- /')[0].strip()  
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace(',','').strip()
        notice_data.est_amount =float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
 
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(11)').text
        if "приостановлена" in notice_data.document_type_description or 'отменена' in notice_data.document_type_description:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
  
    try:  
        page_detail_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(2) a')))
        page_main.execute_script("arguments[0].click();",page_detail_click)
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'span.top_bg > div > table > tbody > tr:nth-child(5)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
 
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'BY'
        customer_details_data.org_language = 'RU'

        customer_details_data.org_name = page_main.find_element(By.XPATH, '( //*[contains(text(),"Полное наименование")])[2]//following::td[1]').text

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '( //*[contains(text(),"Место нахождения")])[2]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
 
        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '( //*[contains(text(),"Адрес электронной почты")])[2]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '( //*[contains(text(),"Адрес сайта в сети Интернет")])[2]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '(//*[contains(text(),"КОНТАКТНОЕ ЛИЦО")])//following::td[2]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lots_no = page_main.find_element(By.XPATH, "//*[@class='paginator']").text.split(' ')[0]
        lot_no =int(lots_no.strip())
        
        lots = page_main.find_element(By.XPATH, '((//*[contains(text(),"СВЕДЕНИЯ О ЛОТЕ")])//following::table/tbody)[1]')
        for no in range(0,lot_no):
            lot_number = 1
            for data in lots.find_elements(By.CSS_SELECTOR, '#j_idt162\:lotsList\:'+str(no)):
                
                lot_details_data = lot_details()
                lot_details_data.lot_number =lot_number

                lot_details_data.lot_title = data.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                try:
                    lot_details_data.lot_actual_number = data.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    lot_quantity = data.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_quantity = re.sub("[^\d\.\,]","",lot_quantity).replace(',','').strip()
                    lot_details_data.lot_quantity =int(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_quantity_uom = data.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_details_data.lot_quantity_uom = re.sub("[\d+\,]","",lot_quantity_uom).strip()
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                try:
                    contract_start_date = data.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text.split('-')[0].strip()
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date, '%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass

                try:
                    contract_end_date = data.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text.split('-')[1].strip()
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date, '%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass

                try:
                    lot_grossbudget_lc = data.find_element(By.CSS_SELECTOR, ' td:nth-child(8)').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc).replace(',','').strip()
                    lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc)
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        attach= page_main.find_element(By.XPATH, '((//*[contains(text(),"ДОКУМЕНТЫ")])//following::table/tbody)[1]')
        attach_no = page_main.find_element(By.XPATH, '(((//*[contains(text(),"ДОКУМЕНТЫ")])//following::table/tbody)[1]/tr)[last()]').text.split(' ')[0]
        attachs = int(attach_no.strip())
        
        for no in range(0,attachs):
            for data in attach.find_elements(By.CSS_SELECTOR, '#j_idt162\:findDocumListByText\:'+str(no)):
                attachments_data = attachments()

                attachments_data.file_name = data.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                attachments_data.external_url = data.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute('href')
                
                try:
                    attachments_data.file_type = data.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__)) 
                    pass
                
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass  
    
    try:  
        return_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//input[@class='iceCmdBtn buttonContent'])[1]")))
        page_main.execute_script("arguments[0].click();",return_click)
        time.sleep(5)
    except:
        pass
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.ui-datatable-even')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) +  str(notice_data.local_title)
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
page_main = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://zakupki.butb.by/auctions/reestrauctions.html#"] 
    for url in urls:
        fn.load_page(page_main, url, 50)  
        logging.info('----------------------------------')
        logging.info(url)
        
        search_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.iceCmdLnk')))
        page_main.execute_script("arguments[0].click();",search_click)
        time.sleep(5)

        lst =['0']
        for no in lst:
            click = page_main.find_element(By.CSS_SELECTOR, '#fra\:selectStatus\:_'+no)
            click.click()
            time.sleep(3)
            
        search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/span[1]/div/table/tbody/tr[5]/td[2]/span/div/div/form[1]/div[1]/div/input[1]')))
        page_main.execute_script("arguments[0].click();",search)
        time.sleep(5)
        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#fra\:reestrAu > div:nth-child(3) > table > tbody> tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#fra\:reestrAu > div:nth-child(3) > table > tbody> tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#fra\:reestrAu > div:nth-child(3) > table > tbody> tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#fra\:reestrAu > div:nth-child(3) > table > tbody> tr'),page_check))
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
