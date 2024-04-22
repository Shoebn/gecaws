#ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34", 
#ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41",
#ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=9dde0154-1de6-40a4-b709-ac7906cada04"

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_aumass"
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
from webdriver_manager.chrome import ChromeDriverManager

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_aumass"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_aumass'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
   
    notice_data.main_language = 'DE'
    
    # Onsite Field -Verfahren
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, '#page div > div:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -aumass-Id
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#page div > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Projekt
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#page div > div:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -offer period
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#page div > div:nth-child(4)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -inspect url for detail page
    # Onsite Comment -None

    try:
        notice_data.notice_url = 'https://plattform.aumass.de/Veroeffentlichung/'+str(notice_data.notice_no)
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content > div').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Kurztext
#     # Onsite Comment -None

    try:
        notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),'Kurztext')]//following::td[1]").text
        notice_data.notice_summary_english = GoogleTranslator(source = 'auto', target = 'en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Kurztext')]//following::td[1]").text
        if len(local_description)<=1:
            notice_data.local_description = notice_data.local_title
        else:
            notice_data.local_description = local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

# Onsite Field -Veröffentlichungsdatum
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Veröffentlichungsdatum')]//following::td[1]").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -None
#     # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=7a243b29-ecc8-4702-a093-a8126f00418e#bidderQuestionTab"

    try:
        document_type_description = page_details.find_element(By.CSS_SELECTOR, 'section:nth-child(2) > fieldset > h2').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -("Dienstleistung" = service , "Lieferleistung"  = supply,"Bauleistung" = work)
    # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

    try:
        notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Art des Vertrages')]//following::td[1]").text
        if 'Dienstleistung' in notice_contract_type :
            notice_data.notice_contract_type = 'Service'
        elif 'Lieferleistung' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Bauleistung' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteII_0__AbschnittII1_GeschaetzterWertOhneMehrwertsteuer').get_attribute('value')
        grossbudgetlc = re.sub("[^\d\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Angaben zu Mitteln der Europäischen Union
    # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

    try:
        funding_agency = page_details.find_element(By.XPATH, "//*[contains(text(),'Europäischen Union')]//following::div[1]").text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'

        customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, '#content > div').text.split("Auftraggeber")[1].split("Titel")[0].strip()
        try:
            if 'Ort der Leistung:' in notice_text:
                customer_details_data.org_address=notice_text.split('Ort der Leistung:')[1].split('Anschrift')[1].split("\n")[0]
            if 'Postanschrift' in notice_text:
                customer_details_data.org_address=page_details.find_element(By.CSS_SELECTOR,'input#AbschnitteI1_0__Postanschrift.form-control').get_attribute('value')
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            postal_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Postleitzahl')]//following::td[1]").text
            customer_details_data.postal_code = re.findall('\d{5}',postal_code)[0]
        except:
            try:
                postal_code = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteI1_0__Postleitzahl').get_attribute('value')
                customer_details_data.postal_code = re.findall('\d{5}',postal_code)[0]
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[@id="AbschnitteI1_0__Telefon"]').get_attribute("value")
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Telefon:')]").text.split("Telefon:")[1].split(",")[0]                 
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[@id="AbschnitteI1_0__Fax"]').get_attribute("value")
        except:
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, "//*[contains(text(),'Fax')]").text.split("Fax:")[1]
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, "tr:nth-child(14) > td > div > span:nth-child(5)").text.split("E-Mail:")[1].strip()
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteI1_0__EMail').get_attribute("value")       
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, "//*[contains(text(),'NUTS-Code')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.XPATH,"/html/body/div[2]/div[3]/div[2]/div/div[3]/div[1]/div/div/div/div/table/tbody/tr[20]/td[2]/span"):
            cpvs_data = cpvs()
            try:
                cpv_code = single_record.text
                cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0].strip()
            except:
                cpvs_data.cpv_code=notice_text.split('CPV-Code Hauptteil:')[1].split('\n')[1]
                cpvs_data.cpv_code = re.findall('\d{8}',cpvs_data.cpv_code)[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    notice_text= page_details.find_element(By.CSS_SELECTOR, '#content > div').text
    if "Los-Nr" in notice_text:
        try:
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR,'fieldset.row.row_ii_02_01'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_actual_number = single_record.find_element(By.CSS_SELECTOR,"fieldset.row.row_ii_02_01 > div:nth-child(3) > div > div input")      
                    lot_details_data.lot_actual_number = lot_actual_number.get_attribute('value')  
                except:
                    pass  

                try:
                    lot_title = single_record.find_element(By.CSS_SELECTOR, 'fieldset.row.row_ii_02_01 > div:nth-child(2) > div > div input')   
                    lot_title = lot_title.get_attribute('value') 
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                    lot_details_data.lot_description = lot_details_data.lot_title
                except:
                    pass

                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass    

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
    else:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        lot_details_data.lot_description = notice_data.notice_title
        lot_details_data.lot_nuts = customer_details_data.customer_nuts
        lot_details_data.contract_type = notice_data.notice_contract_type
        lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)

    try:              
        attachments_data = attachments()
    # Onsite Field -None
    # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

        attachments_data.file_type = '.zip'
            
        attachments_data.file_name = 'TENDER DOCUMENTS'

    # Onsite Field -Download
    # Onsite Comment -None
    
        external_url = page_details.find_element(By.CSS_SELECTOR, '#fileData > div > div > a').get_attribute('href')
        if 'javascript:void(0)' in external_url:
            attachment_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="fileData"]/div/div/a')))
            page_details.execute_script("arguments[0].click();",attachment_clk)
            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[@id="freierDownloadLinkArea"]/a').get_attribute('href')
        else:
            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[@id="fileData"]/div/div/a').get_attribute('href')
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
page_main.maximize_window()
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
page_details.maximize_window()
time.sleep(20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.aumass.de/ausschreibungen?params='] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div > div > p:nth-child(4) > a')))
            page_main.execute_script("arguments[0].click();",click)
        except:
            pass
        
        try:
            for page_no in range(1,5):                                                                      
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div#page.page'+str(page_no)+' a'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div#page.page'+str(page_no)+' a ')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div#page.page'+str(page_no)+' a')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"span.pagination-next")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(2)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div#page.page'+str(page_no)+' a'),page_check))
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
