from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pl_platformza_spn"
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
import re
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options


# Note:Open the site than click on "li:nth-child(5) > ul > li:nth-child(1) > a" this button then grab the data 

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "pl_platformza_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'pl_platformza_spn'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'PLN'
    
    notice_data.main_language = 'PL'
    
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 4
  
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info > b').text.split('(ID ')[0]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Comment -Note:Splite notice_no in local_title ex,."ZP.26.2.135.2023 Dostawa aparatu rtg wraz systemem do radiografii cyfrowej (ID 863319)" take for "ZP.26.2.135.2023".   Note:If notice_no is blank than take from url in page_deatail
    try:
        title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info > b > a').text
        org_text = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info').text
        org_name = fn.get_string_between(org_text,title,'Postępowanie trwające').strip()
    except:
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'div.col-md-9.col-sm-8.col-xs-8.product-info > span').text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info > b > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:  
        clk=page_details.find_element(By.XPATH,'//*[@id="navbar-menu-collapse"]/ul/li[6]/ul/li[1]/a').click()
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_no = notice_data.notice_url.split('/')[-1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.container > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -Termin >> Zamieszczenia
#     # Onsite Comment -Note:Grab time also

    try: 
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Zamieszczenia")]//following::td[1]').text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+:\d',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try: #27-03-2024 08:17:00
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Data rozpoczęcia")]//following::b[1]').text
            publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+:\d',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            try: #27-03-2024 08:17:00
                publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Starting date")]//following::b[1]').text
                publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+:\d',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass    

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -Termin >> Składania
#     # Onsite Comment -Note:Grab time also

    if notice_data.notice_deadline is None:
        try: 
            notice_deadline = page_details.find_element(By.XPATH,'//*[contains(text(),"Składania")]//following::td[1]').text
            notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except:
            try:
                notice_deadline = page_details.find_element(By.XPATH,'(//*[contains(text(),"Do końca")]//following::span[10])[1]').text
                notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except:
                try:
                    notice_deadline = page_details.find_element(By.XPATH,'(//*[contains(text(),"To the end")]//following::span[10])[1]').text
                    notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d',notice_deadline)[0]
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                    logging.info(notice_data.notice_deadline)
                except Exception as e:
                    logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                    pass

    try:
        netbudgetlc  = page_details.find_element(By.XPATH, '//*[contains(text(),"Current offer value is")]//following::td[1]').text
        netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
        notice_data.netbudgetlc =float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc : {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Termin >> Rodzaj
#     # Onsite Comment -Note:Repleace following keywords with given keywords("Dostawy=Supply","Usługa=Service","Robota budowlana=Works")
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Rodzaj")]//following::td[1]').text
        if 'Dostawy' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Usługa' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Robota budowlana' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

#     # Onsite Field -Termin >> Tryb
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tryb")]//following::td[1]').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/pl_platformza_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass   
    
    try:              
        customer_details_data = customer_details()
    # Onsite Comment -Note:Take after title
        customer_details_data.org_name = org_name
        if customer_details_data.org_name == '':
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.row.company-auction-section div:nth-child(2) div > div > a').text
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.row.company-auction-section div:nth-child(2) div div b').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Comment -Note:Take a first data

        try:
            customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.row.company-auction-section div:nth-child(2) div > div > a').get_attribute('href')
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

    # Onsite Field -tel.
    # Onsite Comment -Note:Take after this "tel." keyword

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"tel.")]').text.split('tel.')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -e-mail
    # Onsite Comment -Note:Take after this "e-mail" keyword

        try:
            org_email = page_details.find_element(By.XPATH, '(//*[@id="requirements"])[1]').text
            customer_details_data.org_email = fn.get_email(org_email)
        except:
            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"e-mail:")]').text
                customer_details_data.org_email = fn.get_email(org_email)
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

        customer_details_data.org_country = 'PL'
        customer_details_data.org_language = 'PL'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#allAttachmentsTable > tbody > tr  '):
            attachments_data = attachments()
        # Onsite Field -Attachments to the proceedings >> NAME
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.replace(attachments_data.file_type,'')

        # Onsite Field -Attachments to the proceedings >> SIZE (kB)
            
            try:
                size=page_details.find_element(By.XPATH,'//*[@id="allAttachmentsTable"]/thead/tr/th[3]/div').text.split('(')[1].split(')')[0]
                file_size1 = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
                file_size = file_size1 + size 
                attachments_data.file_size = file_size
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

        # Onsite Field -Attachments to the proceedings >> DOWNLOAD

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(6) a').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#offerForm > div:nth-child(7) > div > div > table > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -Attachments to the proceedings >> NAME
        # Onsite Comment -Note:Don't take file extention

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > p > a').get_attribute('href')
            
            try: 
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            if attachments_data.external_url != '':
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except:
        pass
            
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '(//*[@id="requirements"])[1]').text.split('W przypadku pytań')[0].strip()
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '(//*[@class="description-summary"])[1]').text.split('W przypadku pytań')[0].strip()
        except:
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '(//*[@class="description-summary"])[1]').text
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__)) 
                pass
            
    try:
        if len(notice_data.local_description) > 4999:
            notice_summary_english1 = notice_data.local_description[:4999]
            notice_summary_english2 = notice_data.local_description[4999:]
            summary_english1 = GoogleTranslator(source='auto', target='en').translate(notice_summary_english1)
            summary_english2 = GoogleTranslator(source='auto', target='en').translate(notice_summary_english2)
            notice_data.notice_summary_english = summary_english1 + ' ' + summary_english2
        else:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__)) 
        pass


    try:       
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#offerForm > div:nth-child(4) > div > div > table > tbody > tr  '):
            lot_details_data = lot_details()

        # Onsite Field -LP

            try:
                lot_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                lot_details_data.lot_number = int(lot_number)
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_vat = float(single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6) div button span').text.split('%')[0])
            except:
                pass

        # Onsite Field -NAZWA
        # Onsite Comment -take data from "Przedmiot zamówienia" only
            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
                
            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Rodzaj")]//following::td[1]').text
                if 'Dostawy' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type  = 'Supply'
                elif 'Usługa' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Service'
                elif 'Robota budowlana' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Works'
            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -OPIS I ZAŁĄCZNIKI	
        # Onsite Comment -take data from "Przedmiot zamówienia" only

            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.replace('attachments_data.file_name ','')
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

        # Onsite Field -ILOŚĆ/ JM
        # Onsite Comment -take data from "Przedmiot zamówienia" only   ..... just take value in quantity eg."50 pcs." take "50 in quantity"
            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                lot_details_data.lot_quantity = float(re.findall(r'(\d+)',lot_quantity)[0])
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

        # Onsite Field -ILOŚĆ/ JM
        # Onsite Comment -take data from "Przedmiot zamówienia" only   ..... just take units in UOM eg."50 pcs." take "pcs in UOM"

            try:
                lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
                lot_details_data.lot_quantity_uom = re.findall(r'(\D+)',lot_quantity_uom)[0]
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass


    # Onsite Field -just take data from "Kryteria i warunki formalne"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#offerForm > div:nth-child(7) > div > div > table > tbody > tr'):
                    lot_criteria_data = lot_criteria()

                    # Onsite Field -just take data from "Kryteria i warunki formalne"

                    lot_criteria_data.lot_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

                    # Onsite Field -CRITERIUM WEIGHT
                    # Onsite Comment -just take data from "Kryteria i warunki formalne"

                    lot_criteria_weight = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('%')[0]
                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)

                    if 'Cena' in lot_criteria_data.lot_criteria_title :
                        lot_criteria_data.lot_is_price_related = True

                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://platformazakupowa.pl/all"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk=page_main.find_element(By,XPATH,'/html/body/div[2]/div/a[1]').click()
        except:
            pass
        
        clk=page_main.find_element(By.CSS_SELECTOR,'li:nth-child(5) > ul > li:nth-child(1) > a').click()
        time.sleep(10)

        select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'select#year.form-control.selectpicker'))
        select_fr.select_by_index(1)
        
        clk=page_main.find_element(By.XPATH,'//*[@id="proceedings_filters"]/div[6]/button').click()
        
        try:
            for page_no in range(2,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="active"]/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="active"]/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="active"]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_count == 10:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check1 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="active"]/div[1]/div'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="active"]/div[1]/div'),page_check1))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break  
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
