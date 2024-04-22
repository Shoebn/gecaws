# NOTE ---Use VPN for the URL

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_ospedale_spn"
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
import gec_common.th_Doc_Download as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_ospedale_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'it_ospedale_spn'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    notice_data.document_type_description = 'Bandi di gara e contratti'


    # Onsite Field -None
    # Onsite Comment -if the title start with "AVVISO ESPLORATIVO di MANIFESTAZIONE DI INTERESSE" notice type will be = 5 --- ref url "https://www.ospedale.perugia.it/bandi/avviso-esplorativo-di-manifestazione-di-interesse-procedura-negoziata-senza-bando-in-modalita-telematica-finalizzata-alla-fornitura-in-service-di-un-frazionatore-iniettore-automatico-per-radiofarmaci-occorrente-alla-s-c-medicina-nucleare-della-aziend"
    #     if the attachment having keyword "Errata Corrige.pdf" than it is Notice type = 16 --- ref url "https://www.ospedale.perugia.it/bandi/avviso-di-consultazione-preliminare-di-mercato-per-la-fornitura-di-broncoscopi-monouso"
    #     if you get following keywords in notice text "AGGIUDICATARIO" and "IMPORTO AGGIUDICAZIONE" take notice type "7" --- ref url "https://www.ospedale.perugia.it/bandi/lavori-di-adeguamento-delle-strutture-ed-impianti-esistenti-in-funzione-della-installazione-di-una-pettac-per-il-reparto-di-medicina-nucleare-al-piano-1-del-blocco-p"
    try:
        try:
            title = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot   p:nth-child(1) > span').text
            title = title.lower()
            if title.startswith('avviso esplorativo di manifestazione di interesse'):
                notice_data.notice_type = 5
            else:
                notice_data.notice_type = 4
        except:
            pass
        
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot   p:nth-child(1) > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > p:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return    

    try:  
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR,"#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot  div >  p:nth-child(3) > span").text
        if 'ORE' in notice_deadline1 or 'ore' in notice_deadline1:
            try:
                notice_deadline = re.findall('\d+/\d+/\d{4} [ORE:|ore]+ \d+:\d+:\d+',notice_deadline1)[0]
                try:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ORE: %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ore %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_deadline = re.findall('\d+/\d+/\d{4} [ORE:|ore|ora locale]+ \d+:\d+',notice_deadline1)[0]
                try:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ORE: %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ore %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ora locale %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        else:
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline1)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass     
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")
        fn.load_page(page_details, notice_data.notice_url, 80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        local_description = page_details.find_element(By.XPATH,'//article[@class="prose layout-prose clearfix"][1]|//p[@id="ctl00_cphBody_parSottotitolo"]/following-sibling::p[1]').text.split("DATA PUBBLICAZIONE")[0].strip()
        if 'LINK GARA' in local_description:
            pass
        elif local_description != '':
            local_description = ''.join(local_description).strip()
            notice_data.local_description = local_description
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        page_details.find_element(By.XPATH, '//button[contains(text(),"Accetta")]').click()
    except:
        pass
    time.sleep(2)
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR,'div.col-sx.col-xs-12.col-md-7').get_attribute("outerHTML")
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    try:
        notice_text = page_details.find_element(By.CSS_SELECTOR,'div.col-sx.col-xs-12.col-md-7').text
        if 'AGGIUDICATARIO' in notice_text or 'IMPORTO AGGIUDICAZIONE' in notice_text:
            notice_data.notice_type = 7
            if notice_data.notice_type == 7:
                try:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = 1
                    
                    lot_details_data.lot_title = notice_data.local_title
                    notice_data.is_lot_default = True
                    lot_details_data.lot_title_english = notice_data.notice_title
                        
                    try:
                        award_details_data = award_details()
                            
                        award_details_data.bidder_name = page_details.find_element(By.XPATH,'//*[contains(text(),"Aggiudicatario")]').text
                        
                        try:
                            award_details_data.netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"Importo aggiudicazione")]').tex
                        except:
                            logging.info("Exception in netawardvaluelc: {}".format(type(e).__name__))
                            pass
                        
                        try:
                            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                        except:
                            logging.info("Exception in netawardvalueeuro: {}".format(type(e).__name__))
                            pass
                        
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                    except Exception as e:
                        logging.info("Exception in award_details: {}".format(type(e).__name__))
                        pass
                    
                    if lot_details_data.award_details != []:
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                except Exception as e:
                    logging.info("Exception in lot_details: {}".format(type(e).__name__))
                    pass
    except:
        pass
    
    try:
        customer_details_data = customer_details()
        customer_details_data.org_name = 'L’Azienda Ospedaliera di Perugia'
        customer_details_data.org_parent_id = '1322722'
        customer_details_data.org_phone = '075 5781'
        customer_details_data.org_email = 'acquistiappalti.aosp.perugia@postacert.umbria.it'
        customer_details_data.org_address = 'sant andrea delle frattle - 06129 PERUGIA'
        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass
    

    try:
        for single_record in page_details.find_elements(By.XPATH, '//div[@class="document"]//a'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href')
            try:
                attachments_data.file_name = single_record.text.split('.')[0]
                if 'Corrige' in attachments_data.file_name:
                    notice_data.notice_type = 16
                else:
                    notice_data.notice_type = 4
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
            try:
                filetype =single_record.text
                if 'pdf' in filetype:
                    attachments_data.file_type = 'pdf'
                elif 'doc' in filetype:
                    attachments_data.file_type = 'doc'
                elif 'zip' in filetype:
                    attachments_data.file_type = 'zip'
                else:
                    attachments_data.file_type = single_record.text.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    #NOTE - from the following link  "https://www.ospedale.perugia.it/pagine/bandi-di-gara-e-contratti" >>>>> use "p:nth-child(4) >a" for page detail >>>  click on "lINK GARA" use selector " p:nth-child(2) > span > a" for page detail1  >>>> add details from page_detail and page_detail1 - following is the code UPDATE it in the script
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(2) > span > a').get_attribute("href")
        fn.load_page(page_details1, notice_data.additional_tender_url, 80)
        logging.info(notice_data.additional_tender_url)

        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR,'div.A65JXVB-eb-d.A65JXVB-eb-g > div > div:nth-child(3) > div:nth-child(2) > div').get_attribute("outerHTML")
        except:
            pass

    # Onsite Field -Categorie
    # Onsite Comment -None

        try:
            category_list=''
            for category in page_details1.find_elements(By.CSS_SELECTOR, 'div.A65JXVB-jb-l'):
                category_data = category.text.strip()

                cpvs_data = cpvs()
                cpvs_data.cpv_code = category_data.split('-')[0].strip()
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

                category_list += category_data
                category_list += ','
            notice_data.category =category_list.rstrip(',')
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass

        try: 
            for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div > div.A65JXVB-A-b > div.A65JXVB-A-a > div > div > div > div.A65JXVB-v-s > div > table > tbody > tr')[1:]:
                attachments_data = attachments()
            # Onsite Field -Descrição
            # Onsite Comment -None

                attachments_data.file_name = single_record.text.strip().split('\n')[1]

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' tr >td:nth-child(1)').click()
                time.sleep(3)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url= (str(file_dwn[0]))

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) + str(notice_data.notice_url)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')

# ----------------------------------------- Main Body

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(5)
page_details = webdriver.Chrome(options=options)
time.sleep(5)
page_details1 = Doc_Download.page_details
time.sleep(5)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ospedale.perugia.it/pagine/bandi-di-gara-e-contratti","https://www.ospedale.perugia.it/pagine/bandi-di-concorso"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_main.find_element(By.XPATH,'//button[contains(text(),"Accetta")]').click()
        except:
            pass
        time.sleep(2)
        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
    
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT, str(page_no))))
                    page_main.execute_script("arguments[0].click();", next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div'), page_check))
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
    logging.info("Exception:" + str(e))
finally:
    page_main.quit()
    page_details.quit()
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
