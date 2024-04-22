from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sk_proebiz"
log_config.log(SCRIPT_NAME)
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sk_proebiz"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'sk_proebiz_spn'
    
    if url == urls[0] or url == urls[3]:
        
        notice_data.main_language = 'CS'

        notice_data.currency = 'CZK'
        
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'CZ'
        notice_data.performance_country.append(performance_country_data)
    if url == urls[1] or url == urls[4]:
        notice_data.main_language = 'PL'

        notice_data.currency = 'PLN'
        
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'PL'
        notice_data.performance_country.append(performance_country_data)
    if url == urls[2] or url == urls[5]:
        notice_data.main_language = 'SK'

        notice_data.currency = 'EUR'
        
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'SK'
        notice_data.performance_country.append(performance_country_data)

    if url == urls[3] or url == urls[4] or url == urls[5]:
        notice_data.notice_type = 16
        notice_data.script_name = 'sk_proebiz_amd'
    else:
        notice_data.notice_type = 4

    notice_data.procurement_method = 2
    notice_data.class_at_source = 'CPV'
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > strong').text

    
    try:
        customer_nuts = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split(org_name)[1].replace("\n",'')
    except:
        pass
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6) > strong').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7) > strong").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.rowlink-skip > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Plánované otváranie ponúk")]//following::dd[1]').text
        document_opening_time = re.findall('\d+.\d+.\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d.%m.%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "td:nth-child(4) > span").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Druh obstarávania')]//following::dd[1]").text
        if 'Služby' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Tovar' in notice_data.contract_type_actual: 
            notice_data.notice_contract_type = 'Supply'  
        elif 'Stavebné práce' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works' 
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:              
        tender_criteria_data = tender_criteria()
        tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Kritérium na vyhodnotenie ponúk')]//following::dd[1]").text
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Výsledok obstarávania")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.container').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Stručný opis")]//following::dd[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    
    try:              
        cpv_code1 = page_details.find_element(By.CSS_SELECTOR, 'body > div.container').text
        cpv_code = re.findall("\d{8}-\d+",cpv_code1)
        for cpv1 in cpv_code:
            cpvs_data = cpvs()
            cpv2 = cpv1.split("-")[0]
            cpvs_data.cpv_code = cpv2
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        class_title_at_source = ''
        cpv_at_source = ''
        cpv_code1 = page_details.find_element(By.CSS_SELECTOR, 'body > div.container').text
        cpv_code = re.findall("\d{8}-\d+",cpv_code1)
        for cpv1 in cpv_code:
            cpv2 = cpv1.split("-")[0]
            class_title_at_source += cpv_code1.split(cpv1)[1].split("\n")[0].replace("-",'')
            class_title_at_source += ','
            cpv_at_source += cpv2
            cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.class_codes_at_source = notice_data.cpv_at_source
        
        notice_data.class_title_at_source = class_title_at_source[:500].rstrip(',')
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresa")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__)) 
            pass
        
        try:
            customer_details_data.customer_nuts = customer_nuts
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__)) 
            pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Procesný garant")]//following::dd[1]').text.split("\n")[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
            pass
        
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Procesný garant")]//following::dd[1]').text.split("\n")[1]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__)) 
            pass
        
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Procesný garant")]//following::dd[1]').text.split("\n")[2]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
            pass
        
        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internetový odkaz na profil obstarávateľa")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__)) 
            pass

        customer_details_data.org_country = performance_country_data.performance_country
    
        customer_details_data.org_language = notice_data.main_language
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number=1  
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.container > div > div> h2'):
            lot_details_data = lot_details()
            try:
                lot_details_data.lot_title = single_record.text.split("-")[1]
            except:
                lot_details_data.lot_title = single_record.text.split(":")[1]
                
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            lot_details_data.lot_number = lot_number
            try:
                lot_details_data.lot_actual_number = single_record.text.split(lot_details_data.lot_title)[0].replace("-",'').replace(":",'').strip()
            except:
                pass
                            
            lot_details_data.lot_class_codes_at_source="CPV"
    
            try:              
                lot_cpv_code1 = page_details.find_element(By.CSS_SELECTOR, 'body > div.container').text
                lot_cpv_code = re.findall("\d{8}-\d+",lot_cpv_code1)
                for cpv1 in lot_cpv_code:
                    lot_cpvs_data = lot_cpvs()
                    cpv2 = cpv1.split("-")[0]
                    lot_cpvs_data.lot_cpv_code = cpv2
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
                pass

            try:
                lot_cpv_at_source = '' 
                lot_cpv_code1 = page_details.find_element(By.CSS_SELECTOR, 'body > div.container').text
                lot_cpv_code = re.findall("\d{8}-\d+",lot_cpv_code1)
                for cpv1 in lot_cpv_code:
                    cpv2 = cpv1.split("-")[0]
                    lot_cpv_at_source += cpv2
                    lot_cpv_at_source += ','
                lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                lot_details_data.lot_class_codes_at_source = lot_details_data.lot_cpv_at_source
            except Exception as e:
                logging.info("Exception in cpv_at_source: {}".format(type(e).__name__)) 
                pass


            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.container > div > table > tbody > tr'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(5) > a').get_attribute('href')
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except:
                pass
            
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except:
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_data: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://josephine.proebiz.com/sk/public-tenders/all?filter%5Bsearch%5D=&filter%5Bstate%5D=executed&filter%5Bcpv%5D=&filter%5Bnuts%5D=94&filter%5Bsubmit%5D=","https://josephine.proebiz.com/sk/public-tenders/all?filter%5Bsearch%5D=&filter%5Bstate%5D=executed&filter%5Bcpv%5D=&filter%5Bnuts%5D=167&filter%5Bsubmit%5D=","https://josephine.proebiz.com/sk/public-tenders/all?filter%5Bsearch%5D=&filter%5Bstate%5D=executed&filter%5Bcpv%5D=&filter%5Bnuts%5D=1&filter%5Bsubmit%5D=","https://josephine.proebiz.com/sk/public-tenders/all?filter%5Bsearch%5D=&filter%5Bstate%5D=storned&filter%5Bcpv%5D=&filter%5Bnuts%5D=94&filter%5Bsubmit%5D=",'https://josephine.proebiz.com/sk/public-tenders/all?filter%5Bsearch%5D=&filter%5Bstate%5D=storned&filter%5Bcpv%5D=&filter%5Bnuts%5D=167&filter%5Bsubmit%5D=',"https://josephine.proebiz.com/sk/public-tenders/all?filter%5Bsearch%5D=&filter%5Bstate%5D=storned&filter%5Bcpv%5D=&filter%5Bnuts%5D=1&filter%5Bsubmit%5D="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > form > div.container > div > div > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > form > div.container > div > div > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > form > div.container > div > div > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Ďalšia')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > form > div.container > div > div > table > tbody > tr'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > form > div.container > div > div > table > tbody > tr'),page_check))
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
