from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_marcheson_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
import undetected_chromedriver as uc 
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
SCRIPT_NAME = "fr_marcheson_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'fr_marcheson_spn'
    notice_data.main_language = 'FR'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.currency = 'EUR'
    notice_data.class_at_source = 'CPV'
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'h2 > a').get_attribute("href")
        logging.info(notice_data.notice_url)
        options = uc.ChromeOptions() 
        options.headless = False
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")
        page_details = uc.Chrome(use_subprocess=True, options=options)
        page_details.maximize_window()
        time.sleep(2)
        page_details.get(notice_data.notice_url)
        time.sleep(2)
        
        try:
            acpt_clk_page_details = WebDriverWait(page_details, 30).until(EC.presence_of_element_located((By.XPATH,'//*[@id="didomi-notice-agree-button"]')))
            page_details.execute_script("arguments[0].click();",acpt_clk_page_details)
            time.sleep(2)
        except:
            pass
        
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'//h1')))
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'h2 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'div.hidden').text.strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR,'div.lg\:flex.mt-6 > div:nth-child(2) > span').text
        contract_type_actual_en = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        notice_data.notice_contract_type = fn.procedure_mapping("assets/fr_marcheson_spn_contract_type.csv",contract_type_actual_en)
    except Exception as e:
        logging.info("Exception in contract_type_atual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lg\:flex.mt-6 > div:nth-child(3) > span').text.strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:  
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lg\:pr-4').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'div.mt-4.lg\:mt-0.lg\:pl-4').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass


    try: 
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="detail_content"]/div/div[1]/div[2]').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in page_details_notice_text2: {}".format(type(e).__name__))
        pass
    
    try:
        text_data = page_details.find_element(By.XPATH, '//*[@id="detail_content"]/div/div[1]/div[2]').text
        text_data_lower = text_data.lower()
        notice_data.text_data = text_data
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text-m.font-medium.text-neutral-base.pr-6').text
        
        try:
            customer_details_data.org_address = text_data.split('Nom et adresses :')[1].split('TÃ©l')[0].strip()
        except:
            try:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'a > div > span').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass 
        
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'a > div > span').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass 
        
        
        try:  
            postal_code = re.search('code postal(.)+\d{5}',text_data.lower())
            code_postal = postal_code.group()
            customer_details_data.postal_code = re.findall('\d{5}',code_postal)[0]
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        try:  
            customer_nuts = fn.get_after(text_data,'NUTS',25)
            data = re.findall('[A-Z0-9]{4,5}',customer_nuts)[0]
            lst = []
            code = lst.extend(data)
            if lst[-1].isalpha():
                code = lst[0:-1]
                customer_details_data.customer_nuts  = "".join(code)
            else:
                customer_details_data.customer_nuts  = data

        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

        try:
            customer_main_activity_word = ['Activité du pouvoir adjudicateur:','ActivitÃ© principale']
            for i in customer_main_activity_word:
                if i in customer_main_activity_word:
                    customer_details_data.customer_main_activity = text_data.split(i)[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass


        try:
            org_email_text =  text_data.lower()
            if "mail" in org_email_text:
                org_email = fn.get_after(org_email_text,'mail',60)
                customer_details_data.org_email =fn.get_email(org_email)
            elif 'e-mail' in org_email_text:
                org_email = fn.get_after(org_email_text,'e-mail',60)
                customer_details_data.org_email =fn.get_email(org_email)
            elif 'email' in org_email_text:
                org_email = fn.get_after(org_email_text,'email',60)
                customer_details_data.org_email =fn.get_email(org_email)
            elif 'courriel' in org_email_text:
                org_email = fn.get_after(org_email_text,'courriel',60)
                customer_details_data.org_email =fn.get_email(org_email)
            elif 'mèl' in org_email_text:
                org_email = fn.get_after(org_email_text,'mèl',60)
                customer_details_data.org_email =fn.get_email(org_email)
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        try:
            contact_person = fn.get_after(text_data_lower,'nom du contact',60)
            if 'adresse mail du contact' in contact_person:
                try:
                    customer_details_data.contact_person = contact_person.split(':')[1].split('adresse mail du contact')[0].strip()
                except:
                    contact_person = text_data_lower.split('nom du contact')[1].split('adresse mail du contact')[0].strip()
                    customer_details_data.contact_person = contact_person.split(':')[1].strip()
            else:
                contact_person = text_data_lower.split('nom du contact')[1].split('\n')[0].strip() 
                customer_details_data.contact_person = contact_person.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    
        
        try:
            org_phone_words = ['téléphone','tél','tã©l']
            for i in org_phone_words:
                if i in text_data_lower:
                    org_phone = fn.get_after(text_data_lower,i,30)
                    try:
                        customer_details_data.org_phone = re.findall('.\d+ \d{9}',org_phone)[0]
                    except:
                        try:
                            customer_details_data.org_phone = re.findall('\d{10}',org_phone)[0]
                        except:
                            try:
                                org_phone_num = re.findall('\d[0-9]',org_phone)
                                customer_details_data.org_phone = re.findall('\d{10}',''.join(org_phone_num))[0]
                            except:
                                pass
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            type_of_authority_code_words = ['type de pouvoir adjudicateur : ',"forme juridique de l'acheteur:"]
            for i in type_of_authority_code_words:
                if i in type_of_authority_code_words:
                    customer_details_data.type_of_authority_code = text_data_lower.split(i)[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

        try:
            org_city = fn.get_after(text_data_lower,"ville",40)
            if 'code postal' in org_city:
                customer_details_data.org_city = org_city.split(':')[1].split('code postal')[0].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            try:
                customer_details_data.org_website = text_data_lower.split('web :')[1].split('/')[-1].strip()
            except:
                customer_details_data.org_website = text_data_lower.split('adresse principale :')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_fax = text_data_lower.split('fax :')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lst = ["d'envoi du présent avis","d'envoi de l'avis","d'envoi du présent avis à la publication"]
        for i in lst:
            if i in text_data:
                dispatch_date = text_data.split(i)[1].strip()
                dispatch_date_en = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
                try:
                    dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
                    notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                except:
                    try:
                        dispatch_date_en = re.findall('\w+ \d+, \d{4}',dispatch_date_en)[0]
                        notice_data.dispatch_date = datetime.strptime(dispatch_date_en,'%B %d, %Y').strftime('%Y/%m/%d')
                    except: 
                        try:
                            dispatch_date_en = re.findall('\d+ \w+ \d{4}',dispatch_date_en)[0]
                            notice_data.dispatch_date = datetime.strptime(dispatch_date_en,'%d %m %Y').strftime('%Y/%m/%d')
                        except:
                            try:
                                dispatch_date = re.findall('\d{4}-\d+-\d+',dispatch_date)[0]
                                notice_data.dispatch_date = datetime.strptime(dispatch_date,'%Y-%m-%d').strftime('%Y/%m/%d')
                            except:
                                pass

    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass

    try: 
        cpv_at_source = ''

        text_data_remove = text_data.lower().replace('(','').replace(')','')
        for each_cpv in text_data_remove.split('cpv')[1:]:
            cpv_code1 = each_cpv
            if re.search("\d{8}", cpv_code1):
                regex = re.findall(r'\b\d{8}\b',cpv_code1)
                for each_cpv in regex:
                    try:
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = each_cpv
                        cpv_at_source += cpv_code
                        cpv_at_source += ','
                        cpvs_data.cpvs_cleanup()
                        notice_data.cpvs.append(cpvs_data)
                    except:
                        pass
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.class_codes_at_source = notice_data.cpv_at_source
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
 
    try:
        contract_duration_word =  ["Durée","Durée du marché"]
        for i in contract_duration_word:
            if i in contract_duration_word:
                contract_duration = text_data.split(i)[1].split('\n')[0].strip()
                if contract_duration!='':
                    if re.search("\d+", contract_duration):
                        notice_data.contract_duration = contract_duration
                else:
                    notice_data.contract_duration = text_data.split(i)[2].split('\n')[0].strip()
                    
        if notice_data.contract_duration is None or notice_data.contract_duration =='':
            try:
                contract_duration = text_data.split("Durée du marché")[1].split('\n')[1].split('\n')[0].strip()
            except:
                contract_duration = text_data.split("Durée du marché")[1].split('\n')[1].split('\n')[0].strip()
            if re.search("\d+", contract_duration):
                notice_data.contract_duration = contract_duration
            
    except:
        pass
    
    try:
        notice_data.local_description = text_data.split('Description:')[1].split('Identifiant de la procédure:')[0].strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        pass
    
    if page_details != None:
        page_details.close()
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
# arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

# page_main = fn.init_chrome_driver(arguments) 
# page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    for page_no in range(1,50): # 50
        url = 'https://www.marchesonline.com/appels-offres/en-cours?page='+str(page_no)
        options = uc.ChromeOptions() 
        options.headless = False
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")
        page_main = uc.Chrome(use_subprocess=True, options=options)
        page_main.maximize_window()
        time.sleep(10) 
        page_main.get(url)
        #fn.load_page(page_master, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        
        try:
            acpt_clk = WebDriverWait(page_main, 30).until(EC.presence_of_element_located((By.XPATH,'//*[@id="didomi-notice-agree-button"]')))
            page_main.execute_script("arguments[0].click();",acpt_clk)
            time.sleep(3)
        except:
            pass
        
        try:
            close_click = WebDriverWait(page_main, 30).until(EC.presence_of_element_located((By.XPATH,'''//a[contains(text(),"Voir les appels d'offres en cours")]/../..//following-sibling::div/button''')))
            page_main.execute_script("arguments[0].click();",close_click)
        except:
            pass
        
        page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH,'//div[@class="w-11/12"]'))).text
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//div[@class="w-11/12"]')))
        length = len(rows)
        try:
            for records in range(0,length):
                
                try:
                    close_click = WebDriverWait(page_main, 30).until(EC.presence_of_element_located((By.XPATH,'''//a[contains(text(),"Voir les appels d'offres en cours")]/../..//following-sibling::div/button''')))
                    page_main.execute_script("arguments[0].click();",close_click)
                except:
                    pass
                
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//div[@class="w-11/12"]')))[records]
                extract_and_save_notice(tender_html_element)
                
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                if notice_count >= MAX_NOTICES:
                    break
        
                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0
        
            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break
            try:
                page_main.quit()  
            except: 
                pass
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
