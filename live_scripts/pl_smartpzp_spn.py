from gec_common.gecclass import *
import logging
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
import gec_common.Doc_Download_ingate
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pl_smartpzp_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'pl_smartpzp_spn'
    
    notice_data.main_language = 'PL'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'PLN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Nazwa
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Numer
    # Onsite Comment -if the given notice_no is not available then take notice_no from notice_url(selector:- 'td:nth-child(6)' )

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data wszczęcia
    # Onsite Comment -take time also if available

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Termin składania wniosków
    # Onsite Comment -if the given notice_deadline is not available then take "Termin składania ofert" as "notice_deadline" (selector:- 'td:nth-child(4)' ) and take time also if available

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
            notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
        
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
    
    # Onsite Field -None
    # Onsite Comment -there is no 'a' tag so we are unavailable to find selector for notice_url... so double click to go to detail page
        
    try:
        notice_url = tender_html_element 
        action = ActionChains(page_main)
        action.double_click(on_element = notice_url) 
        action.perform() 
        time.sleep(5)
        notice_data.notice_url = page_main.current_url
        page_main.refresh()
        time.sleep(5)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -None
    # Onsite Comment -take data from tender_html_page also '//*[@id="listaPostepowanForm:postepowaniaTabela_data"]/tr'
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#postepowanieTabs\:ca').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Skrócony opis przedmiotu zamówienia
    # Onsite Comment -None

    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Skrócony opis przedmiotu zamówienia")]//following::span[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Rodzaj zamówienia
    # Onsite Comment -replace the below keyword with given respective keywords("Brak = Service,Usługi = Service,Dostawy = Supply,Roboty budowlane = Work,Usługi społeczne = Service")

    try:
        notice_data.notice_contract_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Rodzaj zamówienia")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -Rodzaj zamówienia
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"Rodzaj zamówienia")]//following::span[1]').text
        if "Dostawy" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Brak" in notice_data.contract_type_actual or "Usługi" in notice_data.contract_type_actual or "Usługi społeczne" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Roboty budowlane" in notice_data.contract_type_actual or "Usługi" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Work"
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    # Onsite Field -Termin otwarcia ofert
    # Onsite Comment -take time also if available

    try:
        document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Termin otwarcia ofert")]//following::span[1]').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    # Onsite Field -Numer ogłoszenia
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_main.find_element(By.XPATH, '//*[contains(text(),"Numer ogłoszenia")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -ref url:--https://portal.smartpzp.pl/rzizielonagora/public/postepowanie?

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Zamawiający
    # Onsite Comment -None

        customer_details_data.org_name = org_name
    # Onsite Field -Dane kontaktowe
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Dane kontaktowe")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Dane kontaktowe
    # Onsite Comment -None

        try:
            org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Dane kontaktowe")]//following::div[1]').text
            customer_details_data.org_phone = re.findall('\d{9}',org_phone)[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Dane kontaktowe
    # Onsite Comment -None

        try:
            org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Dane kontaktowe")]//following::div[1]').text
            customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+',org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Adres strony internetowej instytucji
    # Onsite Comment -None

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Adres strony internetowej instytucji")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'PL'
        customer_details_data.org_country = 'PL'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -ref url:--https://portal.smartpzp.pl/rzizielonagora/public/postepowanie?postepowanie=60685756

    try:              
        cpvs_data = cpvs()
        # Onsite Field -Kod CPV
        # Onsite Comment -None

        cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Kod CPV")]//following::span[1]').text.split("-")[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.class_title_at_source = page_main.find_element(By.XPATH, '//*[contains(text(),"Kod CPV")]//following::span[1]').text.split("-")[2].strip()
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__)) 
        pass
    
    try:
        cpv_at_source = ''
        cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Kod CPV")]//following::span[1]').text
        cpv_at_source += re.findall('\d{8}',cpv_code)[0]
        cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.class_codes_at_source = notice_data.cpv_at_source
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass

    try:
        category = page_main.find_element(By.XPATH, '//*[contains(text(),"Kod CPV")]//following::span[1]').text
        notice_data.category = re.split("\d+-\d+ -", category)[1]
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -ref url:--https://portal.smartpzp.pl/rzizielonagora/public/postepowanie?postepowanie=60685756

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#postepowanieTabs\:kartaPostepowaniaForm\:j_idt568 div.pzp-form > div.row '):
            tender_criteria_data = tender_criteria()

        # Onsite Field -Kryteria oceny ofert
        # Onsite Comment -take values only from "Kryteria oceny ofert " and if "tender_criteria_title " have keyword "Cena" then  "tender_is_price_related " will be 'true'

            tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'div.title').text

        # Onsite Field -Kryteria oceny ofert
        # Onsite Comment -take values only from "Kryteria oceny ofert "

            tender_criteria_weight = single_record.find_element(By.CSS_SELECTOR, 'div.criteria').text.split("Waga %: ")[1].split(".")[0].strip()
            tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

            if "Cena" in tender_criteria_data.tender_criteria_title:
                tender_criteria_data.tender_is_price_related = True

            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

# # Onsite Field -Dokumentacja Postępowania
# # Onsite Comment -click on "Dokumentacja Postępowania" tab to get attachments and then tick mark on "Nazwa dokumentu" for all documents then click on "Pobierz" to download attachments

    Attachment_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#postepowanieTabs > ul > li:nth-child(2) a')))
    page_main.execute_script("arguments[0].click();",Attachment_click)
    time.sleep(2)
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#postepowanieTabs\:dp').get_attribute("outerHTML")                     
    except:
        pass
    
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'(//th[2])[1]'))).text
        for click in range (2,20):
            time.sleep(3)

            try:
                select_all = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[5]/div[2]/div[2]/div[3]/div/div/div/div[2]/div/form/div[1]/div[2]/div/div[2]/div/table/thead/tr/th[1]/div/div[2]')))
                page_main.execute_script("arguments[0].click();",select_all)
                time.sleep(5)
            except:
                pass

            
            try:   
                attachment_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(click))))
                page_main.execute_script("arguments[0].click();",attachment_page)
                time.sleep(2)
            except Exception as e:
                logging.info("Exception in attachment_page: {}".format(type(e).__name__))
                logging.info("No attachment Next page")
                break
            
        try:
            attachments_data = attachments()
            # Onsite Field -Pobierz
            # Onsite Comment -click on "Dokumentacja Postępowania" tab to get attachments and then tick mark on "Nazwa dokumentu" for all documents then click on "Pobierz" to download attachments and take in text form

            attachments_data.file_name = "Download Document"

            # Onsite Field -Pobierz
            # Onsite Comment -click on "Dokumentacja Postępowania" tab to get attachments and then tick mark on "Nazwa dokumentu" for all documents then click on "Pobierz" to download attachments

            external_url = page_main.find_element(By.CSS_SELECTOR, '#postepowanieTabs\:listaDokumentowForm\:downloadBtn')
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(200)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])   
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except:
            pass

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        no_data_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#postepowanieTabs > ul > li:nth-child(3) a')))
        page_main.execute_script("arguments[0].click();",no_data_click)
        time.sleep(2)
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#postepowanieTabs\:korespondencja > div').get_attribute("outerHTML")                     
    except:
        pass
        
    page_main.execute_script("window.history.go(-1)")
        
    WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listaPostepowanForm:postepowaniaTabela_data"]/tr')))
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
action = ActionChains(page_main)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://portal.smartpzp.pl/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            accept = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#j_idt32\:cookie-acpt')))
            page_main.execute_script("arguments[0].click();",accept)
            time.sleep(2)
        except:
            pass
        
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="wyszukPostepowanForm:dataWszczeciaOd_input"]'))).click()
        time.sleep(5)
        date_data = th.strftime('%d-%m-%Y')
        yest_date = page_main.find_element(By.XPATH,'//*[@id="wyszukPostepowanForm:dataWszczeciaOd_input"]').send_keys(date_data)
        time.sleep(5)
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'i.fa.icon-pzp-lupka'))).click()
        time.sleep(5)

        try:
            for page_no in range(2,10):#10
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="listaPostepowanForm:postepowaniaTabela_data"]/tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listaPostepowanForm:postepowaniaTabela_data"]/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listaPostepowanForm:postepowaniaTabela_data"]/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(30)
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="listaPostepowanForm:postepowaniaTabela_data"]/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
