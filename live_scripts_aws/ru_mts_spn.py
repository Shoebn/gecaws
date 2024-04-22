from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ru_mts_spn"
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ru_mts_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ru_mts_spn'
    
    notice_data.main_language = 'RU'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'RUB'
    
    notice_data.notice_type = 4
    
    notice_data.document_type_description = 'Статус'
    
    try:
        notice_deadline = tender_html_element.text.split('Дата окончания')[1]
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.get_attribute("href")
    except:
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div[3]/div/div/div').get_attribute("outerHTML")                     
        except:
            pass
        
        try: 
            category = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Категория")]//following::div[1]/div[2]')))
            page_details.execute_script("arguments[0].click();",category)
            time.sleep(5)
            notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Категория")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div[3]/div/div/div/div[2]/div[1]/div[2]/div/h1').text.split('N')[1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            notice_data.local_title = page_details.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div[3]/div/div/div/div[2]/div[1]/div[3]/h2').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:
            local_description1 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Описание")]//following::div[1])[2]/div/p[1]').text
            local_description2 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Описание")]//following::div[1])[2]/div/p[2]').text
            notice_data.local_description = local_description1+''+local_description2
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Размещено")]//following::div[1]').text
            publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
    
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'RU'
            customer_details_data.org_language = 'RU'

            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Организатор")]//following::div[1]').text
            
            try: 
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Менеджер по закупкам")]//parent::p[1]').text.split('Менеджер по закупкам')[1].strip()
            except:
                try:
                    customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо:")]//following::p[1]').text.strip()
                except:
                    try:
                        customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо по организационным вопросам:")]//parent::p[1]').text.split('Контактное лицо по организационным вопросам:')[1].split(',')[0].strip()                        
                    except:
                        try:
                            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Описание")]//following::div[1])[2]').text.split('Ответственный от МТС:')[1].split(',')[0].strip()                        
                        except Exception as e:
                            logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
                            pass 
            
            try: 
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Место нахождения/ Почтовый адрес")]//parent::p[1]').text.split('Место нахождения/ Почтовый адрес:')[1].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                pass 
            
            try: 
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Адрес электронной почты")]//parent::p[1]').text.split('Адрес электронной почты:')[1].strip()
                email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                customer_details_data.org_email = email_regex.findall(org_email)[0]
            except:
                try:
                    org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо:")]//following::p[4]').text.split('E-mail:')[1].strip()
                    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
                except:
                    try:
                        org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо по организационным вопросам:")]//parent::p[1]').text.split('E-mail:')[1].split(',')[0].strip()
                        email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                        customer_details_data.org_email = email_regex.findall(org_email)[0]
                    except:
                        try:
                            org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Описание")]//following::div[1])[2]').text.split('e-mail:')[1].split('\n')[0].strip()
                            email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                            customer_details_data.org_email = email_regex.findall(org_email)[0]
                        except Exception as e:
                            logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                            pass 
            
            try: 
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Номер контактного телефона")]//parent::p[1]').text.split('Номер контактного телефона')[1].strip()
            except:
                try:
                    org_phone1= page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо:")]//following::p[2]').text.split('Тел:')[1].strip()
                    org_phone2= page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо:")]//following::p[3]').text.split('Моб:')[1].strip()
                    customer_details_data.org_phone = org_phone1+','+org_phone2
                except:
                    try:
                        customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо по организационным вопросам:")]//parent::p[1]').text.split('тел:')[1].split(',')[0].strip()
                    except:
                        try:
                            customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"Описание")]//following::div[1])[2]').text.split('тел.:')[1].split(',')[0].strip()
                        except Exception as e:
                            logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                            pass 

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass 
        
        try:
            document_purchase_start_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Дата начала приема документации:")]//parent::p[1]').text
            document_purchase_start_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_start_time)
            document_purchase_start_time = re.findall('\w+ \d+, \d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%B %d, %Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__)) 
            pass
        
        try:
            document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Срок окончания приема документов")]//parent::p[1]').text
            document_purchase_end_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_end_time)
            document_purchase_end_time = re.findall('\w+ \d+, \d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%B %d, %Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__)) 
            pass
        
        try:       
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Сведения о начальной (максимальной) цене Договора")]//following::p[1]').text.split('(')[0].strip()
            est_amount = re.sub("[^\d\.\,]","",est_amount).replace(',','.').strip()
            notice_data.est_amount =float(est_amount)
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e:         
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass  
        
        try: 
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '(//*[contains(text(),"Срок, место и порядок предоставления документации:")]//following::p[1])[1]/a').get_attribute('href')
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass

        try: 
            for single_record in page_details.find_elements(By.XPATH, '(//*[contains(text(),"Документы")]//ancestor::div[1])[4]/div/div/a'):
                attachments_data = attachments()

                attachments_data.external_url = single_record.get_attribute('href')
                
                attachments_data.file_name = single_record.text.split('\n')[0].strip()

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                try:
                    file_size = single_record.text.split('\n')[1].strip()
                    attachments_data.file_size = GoogleTranslator(source='auto', target='en').translate(file_size)
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details =webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tenders.mts.ru/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
            
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[1]/div[3]/div[3]/div[2]/div[3]/a[1]'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, "//a[starts-with(@href, '/tenders/')]")))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, "//a[starts-with(@href, '/tenders/')]")))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.sc-1af8aca5-0.iAMpNk.arrow-right")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div[1]/div[3]/div[3]/div[2]/div[3]/a[1]'),page_check))
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
