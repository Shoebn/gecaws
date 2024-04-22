from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_empulia_spn"
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
import gec_common.th_Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_empulia_spn"
Doc_Download = gec_common.th_Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_empulia_spn'

    notice_data.currency = 'EUR'
  
    notice_data.procurement_method = 2

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'IT'
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: ", str(type(e)))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline= re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: ", str(type(e)))
        pass
    
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")   
        fn.load_page_expect_xpath(page_details1,notice_data.notice_url,'/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div[1]/div[1]/table/tbody/tr/td/table/tbody/tr/td/div/div/div[3]/div[1]/div/table/tbody',180)
        time.sleep(3)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = WebDriverWait(page_details1, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#template_doc > thead > tr > th > h1'))).text.split('(')[1].split(')')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = page_details1.find_element(By.CSS_SELECTOR, 'th > h1').text.split('(')[0]
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
       

    try:
        est_amount = page_details1.find_element(By.XPATH, '''//*[contains(text(),'Importo')]//following::td[1]''').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass



    try:
        notice_data.additional_tender_url = page_details1.find_element(By.XPATH, '''//*[contains(text(),'Altro indirizzo web')]//following::td[1]''').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass


    try:
        notice_data.contract_type_actual = page_details1.find_element(By.XPATH, '''//*[contains(text(),'Tipo Appalto:')]//following::td[1]''').text
        if 'Servizi' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Lavori pubblici' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.category = page_details1.find_element(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(14) > td > table > tbody > tr:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:             
        for single_record in page_details1.find_elements(By.CSS_SELECTOR,'#template_doc > tbody > tr > td > table > tbody tr')[1:]:
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            try:
                file_type = single_record.find_element(By.CSS_SELECTOR, 'label#Allegato_V_N').text
                if ".pdf" in file_type:
                    attachments_data.file_type = 'pdf'
                elif ".zip" in file_type:
                    attachments_data.file_type = 'zip'
                elif ".docx" in file_type:
                    attachments_data.file_type = 'docx'
                elif ".DOC" in file_type:
                    attachments_data.file_type = 'doc'
                elif "pdf" in file_type:
                    attachments_data.file_type = 'pdf'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            external_url1 = single_record.find_element(By.CSS_SELECTOR, ' label.Attach_label').get_attribute('onclick')
            external_url2 = external_url1.split("('")[1].split("'")[0].strip() 
            external_url3 = external_url1.split("escape('")[1].split("')")[0].replace(") + '",'').strip()
            attachments_data.external_url=external_url2+external_url3


            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        pass
    if 'Esito' in page_details1.find_element(By.XPATH,'//*[@id="WebPartctl00_m_g_4e57c279_b7e5_4fb3_8176_25b7c2231127"]').text:
        try:
            for single_record in page_details1.find_elements(By.CSS_SELECTOR,'label#Allegato_V_N'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.text

                try:
                    file_type = single_record.text
                    if ".pdf" in file_type:
                        attachments_data.file_type = 'pdf'
                    elif ".zip" in file_type:
                        attachments_data.file_type = 'zip'
                    elif ".docx" in file_type:
                        attachments_data.file_type = 'docx'
                    elif ".DOC" in file_type:
                        attachments_data.file_type = 'doc'
                    elif "pdf" in file_type:
                        attachments_data.file_type = 'pdf'
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                external_url1 = single_record.get_attribute('onclick')
                external_url2 = external_url1.split("('")[1].split("'")[0].strip() 
                external_url3 = external_url1.split("escape('")[1].split("')")[0].replace(") + '",'').strip()
                attachments_data.external_url=external_url2+external_url3

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    

    tabella_inform = WebDriverWait(page_details1, 50).until(EC.presence_of_element_located((By.XPATH,'//h2[contains(text(),"Tabella informativa di indicizzazione")]')))
    page_details1.execute_script("arguments[0].click();",tabella_inform)
    time.sleep(2)
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#table_dpcm > table ').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass  
    
    try:
        publish_date = WebDriverWait(page_details1, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table_dpcm > table > tbody > tr:nth-child(3) > td:nth-child(11)"))).text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
        
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        type_of_authority_code = page_details1.find_element(By.CSS_SELECTOR, '#table_dpcm > table > tbody > tr:nth-child(3) > td:nth-child(4)').text
    except:
        pass
    try:
        Dettagli = WebDriverWait(page_details1, 10).until(EC.presence_of_element_located((By.XPATH,'//h2[contains(text(),"Dettagli")]')))
        page_details1.execute_script("arguments[0].click();",Dettagli)
        time.sleep(2)
    except:
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#template_doc > tbody ').get_attribute("outerHTML") 
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass  


    try:              
        customer_details_data = customer_details()
        try:
            customer_details_data.org_name = page_details1.find_element(By.XPATH, '''//*[contains(text(),'Ente app')]//following::td[1]''').text
        except:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        
        try:
            customer_details_data.contact_person = page_details1.find_element(By.XPATH, '''//*[contains(text(),'Inc')]//following::td[1]''').text
        except Exception as e:
            logging.info("Exception in contact_person: ", str(type(e)))
            pass
        
        try:
            customer_details_data.type_of_authority_code = type_of_authority_code
        except Exception as e:
            logging.info("Exception in type_of_authority_code: ", str(type(e)))
            pass

        customer_details_data.org_country = 'IT'

        customer_details_data.org_language = 'IT'
        
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details_data: {}".format(type(e).__name__)) 
        pass
    
    try:
        Chiarimenti = WebDriverWait(page_details1, 10).until(EC.presence_of_element_located((By.XPATH,'//h2[contains(text(),"Chiarimenti")]')))
        page_details1.execute_script("arguments[0].click();",Chiarimenti)
        time.sleep(2)
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#tabQuesiti').get_attribute("outerHTML") 
            
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass 
    except:
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details1.find_element(By.XPATH, '//*[@id="esitoWrapper"]/div').get_attribute("outerHTML") 
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
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
page_details1 = fn.init_chrome_driver(arguments)
 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Bandi%20di%20gara%20new.aspx',
            'http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Bandi%20di%20gara%20new.aspx?expired=1&type=All'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10): 
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr[3]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr')))
                length = len(rows)
                logging.info(length)
                for records in range(2,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
            
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody > tr:nth-child(23) > td > a:nth-child('+str(page_no)+')')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr[3]'),page_check))
                except :
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
    page_details1.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
