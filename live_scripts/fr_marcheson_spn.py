from gec_common.gecclass import *
import logging
import requests
import re
import os
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
import xml.etree.ElementTree as ET
import gec_common.web_application_properties as application_properties

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_marcheson_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
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
        notice_data.local_title = tender_html_element.find('title').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:  
        publish_date = tender_html_element.find('pubDate').text
        publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.notice_url = tender_html_element.find('link').text
    
    arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
    page_details = fn.init_chrome_driver_head(arguments)

    fn.load_page(page_details, notice_data.notice_url, 80)
    logging.info(notice_data.notice_url)

    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,' //*[@id="didomi-notice-agree-button"]'))).click()
        time.sleep(5)
    except:
        pass  
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[@id="print_area_info"]/div[1]/div[3]/div[1]/span').text
        contract_type_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        notice_contract_type = fn.procedure_mapping("assets/fr_marcheson_spn_contract_type.csv",contract_type_actual)
        notice_data.notice_contract_type = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__)) 
        pass
    
    try:
        text_data = page_details.find_element(By.CSS_SELECTOR, '#print_area > div.limit-descript-height.descript-line').text
        text_data_lower = text_data.lower()
        notice_data.notice_text = text_data
    except:
        pass

    try: 
        cpv_at_source = ''
        text_data_remove = text_data.lower().replace('(','').replace(')','')
        for each_cpv in text_data_remove.split('cpv')[1:]:
            cpv_code1 = each_cpv
            if re.search("\d{8}", cpv_code1):
                regex = re.findall(r'\b\d{8}\b',cpv_code1)
                for each_cpvs in regex:
                    cpvs_data = cpvs()
                    
                    cpvs_data.cpv_code = each_cpvs
                    
                    cpv_at_source += each_cpvs
                    cpv_at_source += ','
                    
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
                    
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.class_codes_at_source = notice_data.cpv_at_source
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
                
                
#***********************************************************************************************************************

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Retour à la liste")]//following::div[1]/a').text

        try:
            customer_details_data.org_address = text_data.split('Nom et adresses :')[1].split('TÃ©l')[0].strip()
        except:
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
            type_of_authority_code_words = ['type de pouvoir adjudicateur : ',"forme juridique de l'acheteur:","Forme juridique de l'acheteur:"]
            for i in type_of_authority_code_words:
                if i in type_of_authority_code_words:
                    customer_details_data.type_of_authority_code = text_data_lower.split(i)[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

        try:
            org_city = fn.get_after(text_data_lower,"ville :",40)
            if 'code postal' in org_city:
                customer_details_data.org_city = org_city.split('code postal')[0].strip()
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

    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = text_data.split('Description:')[1].split('Identifiant de la procédure:')[0].strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass   

    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,' //*[@id="modalViewPopinExit"]/div[2]/div/div/div[2]/button'))).click()
        time.sleep(5)
    except:
        pass
    
    page_details.quit()

#***********************************************************************************************************************
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_head(arguments)  

# make directory for store all download xml file.
tmp_dwn_dir = application_properties.TMP_DIR + "/fr_marcheson_down_file"+ "_" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

if not os.path.exists(tmp_dwn_dir):
    os.makedirs(tmp_dwn_dir)
else:
    os.makedirs(tmp_dwn_dir)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.marchesonline.com/rss-appels-d-offres'] 
    for url in urls:
        fn.load_page(page_main, url, 90)
        logging.info('----------------------------------')
        logging.info(url)  

        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,' //*[@id="didomi-notice-agree-button"]'))).click()
        time.sleep(5)
        
        rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.homepage > div > div > div:nth-child(6) > div > ul > li > ul > li > p > a')))
        length = len(rows)
        for records in range(0,length):
            each_url = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.homepage > div > div > div:nth-child(6) > div > ul > li > ul > li > p > a')))[records]
            
#**************************************************************************************************************
            # this code create for download xml files from main url and dump in folder 
            sub_url = each_url.get_attribute("href")

            save_path = sub_url.split('rss/')[1].strip()
            response = requests.get(sub_url)
            if response.status_code == 200:
                with open(tmp_dwn_dir+'/'+save_path, 'wb') as file:
                    file.write(response.content)
                logging.info("File downloaded successfully.")
            else:
                logging.info(f"Failed to download file.")
            
#**************************************************************************************************************
        # this code use for grab totel list of files from xml_file
        time.sleep(10)
        path = tmp_dwn_dir
        dir_list = os.listdir(path)
        
        #this code use for iterate each file in loop
        for files in dir_list:
            with open(os.path.join(path, files), 'r') as file:
                data = file.read()

                # grab each notice from xml file into item tag 
                root = ET.fromstring(data)
                for tender_html_element in root.findall('.//item'): #tender_html_element means each item tag
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
