from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_megalis"
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
SCRIPT_NAME = "fr_megalis"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'fr_megalis'
    notice_data.main_language = 'FR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    notice_data.additional_source_name = "Voir l'avis BOAMP"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.small > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.small.pull-left').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:                                                                  
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.date.date-min").text
        publish_date = publish_date.replace('\n', ' ')
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)

        publish_date = publish_date.replace(',','')
        publish_date = publish_date.replace('.','')
        publish_date = publish_date.replace('Sept','Sep')
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        try:
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')

        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.cloture-line").text
        notice_deadline = notice_deadline.replace('\n', ' ')
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        if 'Sept' in notice_deadline:
            notice_deadline = notice_deadline.replace('Sept','Sep')
            notice_deadline = re.findall('\d+ \w+. \d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b. %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        else:
            notice_deadline = re.findall('\d+ \w+. \d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b. %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie > span').text
        if 'Travaux' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Fournitures' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Services'
        else:
            pass

    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul > li:nth-child(1) > a').get_attribute("href")     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#layout-entreprise').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet :")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_summary_english
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        page_details.find_element(By.CSS_SELECTOR,"#collapseHeading > div.panel-heading.clearfix > h1").click()   
        time.sleep(3)
    except:
        pass 
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(6) > div').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual) 
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_megalis_procedure.csv",type_of_procedure_actual)  
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organisme :")]//following::span[1]').text 
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(2) > ul > li:nth-child(3) > div').text 
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:  
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV :")]//following::div[1]').text
        cpv_regex = re.compile(r'\d{8}')
        cpv_code_list = cpv_regex.findall(cpv_code)
        for cpv in cpv_code_list:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        lot_click = page_details.find_element(By.CSS_SELECTOR,"ul > li:nth-child(2) > div > span > a").get_attribute('href')
        lot_click = lot_click.split("popUpSetSize(")[1].split("'")[1]
        lot_page_url = 'https://marches.megalis.bretagne.bzh'+ lot_click
        fn.load_page(page_details1,lot_page_url,80)       

        lot_number = 1
        for single_record in page_details1.find_elements(By.XPATH, '/html/body/form/div[4]/div/div/div/div[2]/div'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
    
            try:
                lot_details_data.lot_actual_number = single_record.text.split(":")[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, '#headingOne > span').text
            lot_title = single_record.text.split(":")[1]

                
            try:
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title) 
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                
            collapese = single_record.find_element(By.CSS_SELECTOR,'#headingOne').click()
            time.sleep(2) 

            try:
                lot_details_data.lot_description = single_record.find_element(By.XPATH, 'div[2]/div/div[2]/div').text 
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description) 
            except Exception as e:
                logging.info("Exception in lot_description_english: {}".format(type(e).__name__))
                pass

            try:
                contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text   
                if 'Travaux' in contract_type:   
                    lot_details_data.contract_type = 'Works'
                elif 'Fournitures' in contract_type:
                    lot_details_data.contract_type = 'Supply'
                elif 'Services' in contract_type:
                    lot_details_data.contract_type = 'Service'
                else:
                    pass

            except Exception as e:      
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass            
            
            try:
                for single_record_1 in single_record.find_elements(By.XPATH, 'div[2]/div/div[3]'):
                    lot_cpv_codes = re.findall(r'\d+', single_record_1.text)
                    
                    for i in lot_cpv_codes:
                        lot_cpvs_data = lot_cpvs()

                        lot_cpvs_data.lot_cpv_code = i
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass            

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#panelPieces > ul > li'):   
            try:
                attachments_data = attachments()

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                file_name = single_record.text 
                attachments_data.file_name = file_name.split('- ')[0].strip()

                try:
                    file_size = file_name.split(' - ')[1]
                    attachments_data.file_size = GoogleTranslator(source='fr', target='en').translate(file_size)
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass
                

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except:
                pass
     
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    th_new = date.today()
    th_new1 = th_new.strftime('%d/%m/%Y')

    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://marches.megalis.bretagne.bzh/?page=Entreprise.EntrepriseAdvancedSearch&searchAnnCons&type=multicriteres'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        date_clear = page_main.find_element(By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_AdvancedSearch_dateMiseEnLigneCalculeStart").clear() 
        search = page_main.find_element(By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_AdvancedSearch_dateMiseEnLigneCalculeStart").send_keys(th_new1)  
        test_clk = page_main.find_element(By.XPATH,'//*[@id="ctl0_CONTENU_PAGE_AdvancedSearch_panelDateMiseEnLigneCalcule"]/div[2]/div[1]/div[2]/span[2]').click()  
        pg_date =  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche")))  
        page_main.execute_script("arguments[0].click();",pg_date)
            
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]   
                extract_and_save_notice(tender_html_element)
                
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
