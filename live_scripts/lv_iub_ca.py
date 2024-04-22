from gec_common.gecclass import *
import logging
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "lv_iub_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'lv_iub_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'LV'
    notice_data.performance_country.append(performance_country_data)
    notice_data.main_language = 'LV'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col > div > div.c3').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        date1=tender_html_element.find_element(By.CSS_SELECTOR, 'div.c1').text
        date1=re.findall('\d+/\d+/\d{4}',date1)[0]
        notice_data.publish_date = datetime.strptime(date1,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'div.c1').text.replace(date1,'')
    except:
        pass
    
    org_name= tender_html_element.find_element(By.CSS_SELECTOR, 'div.col > div > div.c4').text.split('(')[0]
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'div.c2 a').get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        pass

    try:
        notice_data.notice_no = notice_data.notice_url.split('/')[-1].split('-')[-1]
    except:
        pass
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATh,"//*[contains(text(),'Veidlapas tips')]//following::div[1]").text
    except:
        pass
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATh,'//*[@id="collapse-id-1"]/div').get_attribute('innerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATh,'//*[@id="collapse-id-2"]').get_attribute('innerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATh,'//*[@id="collapse-id-5"]/div').get_attribute('innerHTML')
    except:
        pass
    try:
        cpvs_data = cpvs()
        cpv_code = page_details.find_element(By.XPATH,"  //*[contains(text(),'CPV galvenais kods')]//following::div[1]").get_attribute('innerHTML')
        cpvs_data.cpv_code = re.findall("\d{8}",cpv_code)[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpvs_data.cpv_code
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:
        cpv_code1 = page_details.find_element(By.XPATH,"  //*[contains(text(),'CPV papildkods')]//following::div[1]").get_attribute('innerHTML')
        if ',' in cpv_code1:
            for code in cpv_code1.split(','):
                cpv_code2 = re.findall("\d{8}",code)[0]
                for cpv in cpv_code2:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass    
    try:
        notice_data.additional_url = page_details.find_element(By.XPATH,"  //*[contains(text(),'Adrese, kurā iesniedzami piedāvājumi')]//following::div[1]").get_attribute('innerHTML')
    except:
        pass

    try:  

        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        customer_details_data.org_city = page_details.find_element(By.XPATH,"//*[contains(text(),'Organizācijas pilsēta')]//following::div[1]").get_attribute('innerHTML')
        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH,"//*[contains(text(),'Iestādes darbība')]//following::div[1]").get_attribute('innerHTML')
        except:
            pass
        try:
            customer_details_data.org_address =  page_details.find_element(By.XPATH,"//*[contains(text(),'Organizācijas iela')]//following::div[1]").get_attribute('innerHTML')
        except:
            pass
        try:
            customer_details_data.org_email =  page_details.find_element(By.XPATH,"//*[contains(text(),'Organizācijas kontaktpunkts')]//following::div[1]").get_attribute('innerHTML')
            customer_details_data.org_email = fn.get_email(customer_details_data.org_email)
        except:
            pass
        try:
            customer_details_data.org_phone =  page_details.find_element(By.XPATH,"//*[contains(text(),'Organizācijas kontaktpunkts')]//following::div[1]").get_attribute('innerHTML')
            customer_details_data.org_phone = customer_details_data.org_phone.split(',')[-1]
        except:
            pass  
        try:
            customer_details_data.org_website =  page_details.find_element(By.XPATH,"//*[contains(text(),'Organizācijas interneta adrese')]//following::div[1]").get_attribute('innerHTML')
        except:
            pass                                                              
        customer_details_data.org_country = 'LV'
        customer_details_data.org_language = 'LV'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        est_amount = page_details.find_element(By.XPATH," (//*[contains(text(),'Paziņojuma vērtība')]//following::div/div/div/div)[1]").get_attribute('innerHTML')
        est_amount = est_amount.split('EUR')[0]
        notice_data.est_amount = float(est_amount)
        grossawardvaluelc  = notice_data.est_amount
    except:
        pass
    try:
        for Pamatveids in page_details.find_elements(By.XPATH,"//*[contains(text(),'Pamatveids')]//following::div[1]/div/div"):
            contract_type_actual = Pamatveids.get_attribute('innerHTML')
            if 'bi-check-circle' in contract_type_actual:
                notice_data.contract_type_actual = Pamatveids.get_attribute('innerHTML').split('</i>')[1].strip()
                if 'būvdarbi' in  notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works' 
                if 'piegādes' in  notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply' 
                if 'pakalpojumi' in  notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
    except:
        pass
            
    
    try:
        table1 = page_details.find_element(By.CSS_SELECTOR," table.table.table-hover tbody tr").get_attribute('data-bs-target').split('-0')[0]
    except:
        pass
    try:
        
        lot_details_data = lot_details() 
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table.table.table-hover tbody tr'):

            award_details_data = award_details()

            award_details_data.bidder_name =  single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').get_attribute('innerHTML')
            try:
                award_details_data.address = single_record.find_element(By.XPATH, "//h6[contains(text(),'Iela')]//following::div[1]").get_attribute('innerHTML')
                award_details_data.address += single_record.find_element(By.XPATH, "(//h6[contains(text(),'Uzvarētāja valsts')])[1]//following::div[1]").get_attribute('innerHTML')
            except:
                pass
            award_details_data.grossawardvaluelc = notice_data.est_amount
            try:
                date2=tender_html_element.find_element(By.CSS_SELECTOR, 'div.date_2').text
                date2=re.findall('\d+/\d+/\d{4}',date2)[0]
                award_details_data.award_date= datetime.strptime(date2,'%d/%m/%Y').strftime('%Y/%m/%d')
            except:
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except:
        pass
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH,"//*[contains(text(),'Līguma darbības termiņa ilgums')]//following::div[1]").get_attribute('outerHTML').split('>')[1].split('<')[0].strip()
    except:
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver() 
page_details = fn.init_chrome_driver() 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://info.iub.gov.lv/lv/meklet/pt/_pp/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(2)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#main > section > article > section.tbody > section > section'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#main > section > article > section.tbody > section > section')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#main > section > article > section.tbody > section > section')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
            
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#main > section > article > section.tbody > section > section'),page_check))
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