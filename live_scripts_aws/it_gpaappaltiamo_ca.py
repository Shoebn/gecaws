from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_gpaappaltiamo_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
import math
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
SCRIPT_NAME = "it_gpaappaltiamo_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_gpaappaltiamo_ca'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    notice_data.document_type_description = "Procedure aggiudicate"
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Codice
    # Onsite Comment -if the given notice_no is not available the take notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scadenza
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        try:
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Tipo
    # Onsite Comment -split and take data before first '-'
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.split("-")[0].strip()
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_gpaappaltiamo_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ente
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Dettagli
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        if notice_data.notice_no == None:
            notice_data.notice_no = notice_data.notice_url.split('?id=')[-1].strip()
    except Exception as e:
        logging.info("Exception in notice_no2: {}".format(type(e).__name__))
    
    # Onsite Field -None
    # Onsite Comment -take tender_html_page data also (selector :- "/html/body/form/div[4]/div/div[3]/table/tbody/tr")
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.col-12').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Durata
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durata")]//following::em[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo")]//following::em[1]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ambito
    # Onsite Comment -Replace the following keywords with respective keywords(Lavori = Works , Servizi = Service , Forniture = Supply )

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Ambito")]//following::em[1]').text
        if 'Lavori' in notice_data.contract_type_actual :
            notice_data.notice_contract_type = 'Works'
        elif 'Servizi' in notice_data.contract_type_actual :
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_data.contract_type_actual :
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Documenti gara
# Onsite Comment -None

    try:              
        attachment = page_details.find_element(By.XPATH, '//*[contains(text(),"Documenti gara")]//following::table[1]')
        for single_record in attachment.find_elements(By.CSS_SELECTOR, '#documentigara > table > tbody > tr'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute('href')
            
            if attachments_data.external_url != None:
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Buste
# Onsite Comment -None

    try:       
        attachment2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Lotti")]//following::table[2]')
        for single_record in attachment2.find_elements(By.CSS_SELECTOR, 'div.link-list-wrapper > ul > li > ul > li > a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute('href')
            
            if attachments_data.external_url != None:
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        page = page_details.find_element(By.CSS_SELECTOR, '#dropdownMenuButton').text
        if 'Scegli lotto' in page:
            lot_number = 1
            lots = page_details.find_element(By.XPATH, '//*[contains(text(),"Lotti")]//following::table[2]')
            for single_record in lots.find_elements(By.CSS_SELECTOR, '#riepilogolotti > table > tbody > tr'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual 
                    
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__)) 
                    pass
                
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                try:
                    lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__)) 
                    pass
                
                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(5)').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_netbudget_lc =float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__)) 
                    pass
                
                try: 
                    Scegli_lotto_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#dropdownMenuButton')))
                    page_details.execute_script("arguments[0].click();",Scegli_lotto_click)
                    time.sleep(5)
                    
                    lots_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_content_rptGraduatoriaMultiLotto_ctl0'+str(lot_details_data.lot_number)+'_lnkVediGraduatoria')))
                    page_details.execute_script("arguments[0].click();",lots_click)
                    time.sleep(5)

                    award1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Graduatoria")]//following::table[3]')
                    lot_criteria_title = award1.find_element(By.CSS_SELECTOR, '#ctl00_content_pnlGraduatoria > table > thead > tr > th:nth-child(4)').text
                    for single_record1 in award1.find_elements(By.CSS_SELECTOR, '#ctl00_content_pnlGraduatoria > table > tbody > tr'):
                        try:
                            award = single_record1.find_element(By.CSS_SELECTOR, "td:nth-child(8)").get_attribute('innerHTML')
                        except:
                            award = single_record1.find_element(By.CSS_SELECTOR, "td:nth-child(6)").get_attribute('innerHTML')

                        if award != '':
                            award_details_data = award_details()

                                    # Onsite Field -ragione sociale
                                    # Onsite Comment -take only when ('#ctl00_content_pnlGraduatoria > table > tbody > tr > td:nth-child(5)') has "star" symbol in this field

                            award_details_data.bidder_name = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text            

                            award_details_data.award_details_cleanup()
                            lot_details_data.award_details.append(award_details_data)

                            try:
                                if 'punt. tecnico' in lot_criteria_title:
                                    lot_criteria_data = lot_criteria()

                            # Onsite Field -punt. tecnico
                            # Onsite Comment -None
                                    lot_criteria_data.lot_criteria_title = lot_criteria_title

                                    lot_criteria_weight = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                                    lot_criteria_weight = re.sub("[^\d\.\,]","",lot_criteria_weight)
                                    lot_criteria_weight = float(lot_criteria_weight.replace(',','.').strip())
                                    lot_criteria_data.lot_criteria_weight = math.ceil(lot_criteria_weight)

                                    lot_criteria_data.lot_criteria_cleanup()
                                    lot_details_data.lot_criteria.append(lot_criteria_data)
                            except Exception as e:
                                logging.info("Exception in lot_criteria_1: {}".format(type(e).__name__))
                                pass  
                except Exception as e:
                    logging.info("Exception in award_details_1: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
    except:
        try:
            lot_number = 1
            lots = page_details.find_element(By.XPATH, '//*[contains(text(),"Lotti")]//following::table[2]')
            for single_record in lots.find_elements(By.CSS_SELECTOR, '#riepilogolotti > table > tbody > tr'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual 
                
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__)) 
                    pass
                
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
                try:
                    lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__)) 
                    pass
                
                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(5)').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_netbudget_lc =float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__)) 
                    pass
                
                try:  
                    award1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Graduatoria")]//following::table[3]')
                    lot_criteria_title = award1.find_element(By.CSS_SELECTOR, '#ctl00_content_pnlGraduatoria > table > thead > tr > th:nth-child(4)').text
                    for single_record1 in award1.find_elements(By.CSS_SELECTOR, '#ctl00_content_pnlGraduatoria > table > tbody > tr'):
                        try:
                            award = single_record1.find_element(By.CSS_SELECTOR, "td:nth-child(8)").get_attribute('innerHTML')
                        except:
                            award = single_record1.find_element(By.CSS_SELECTOR, "td:nth-child(6)").get_attribute('innerHTML')

                        if award != '':
                            award_details_data = award_details()

                                    # Onsite Field -ragione sociale
                                    # Onsite Comment -take only when ('#ctl00_content_pnlGraduatoria > table > tbody > tr > td:nth-child(5)') has "star" symbol in this field

                            award_details_data.bidder_name = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text            

                            award_details_data.award_details_cleanup()
                            lot_details_data.award_details.append(award_details_data)

                            try:
                                if 'punt. tecnico' in lot_criteria_title:
                                    lot_criteria_data = lot_criteria()

                            # Onsite Field -punt. tecnico
                            # Onsite Comment -None
                                    lot_criteria_data.lot_criteria_title = lot_criteria_title

                                    lot_criteria_weight = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                                    lot_criteria_weight = re.sub("[^\d\.\,]","",lot_criteria_weight)
                                    lot_criteria_weight = float(lot_criteria_weight.replace(',','.').strip())
                                    lot_criteria_data.lot_criteria_weight = math.ceil(lot_criteria_weight)

                                    lot_criteria_data.lot_criteria_cleanup()
                                    lot_details_data.lot_criteria.append(lot_criteria_data)
                            except Exception as e:
                                logging.info("Exception in lot_criteria_2: {}".format(type(e).__name__))
                                pass
                except Exception as e:
                    logging.info("Exception in award_details_2: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
        except Exception as e:
            logging.info("Exception in lot_details_2: {}".format(type(e).__name__))
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
    th = date.today() - timedelta(60)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://gpa.appaltiamo.eu/procedure.aspx?type=a'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[4]/div/div[3]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[4]/div/div[3]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[4]/div/div[3]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.t-button.rgActionButton.rgPageNext')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[4]/div/div[3]/table/tbody/tr'),page_check))
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
    
