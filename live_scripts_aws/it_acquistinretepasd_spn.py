from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_acquistinretepasd_spn"
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

#NOTE- after clicking on url >>> select "Sistema Dinamico"

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_acquistinretepasd_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global cpv_code
    notice_data = tender()

    notice_data.script_name = 'it_acquistinretepasd_spn'

    notice_data.main_language = 'IT'

    notice_data.currency = 'EUR'

    notice_data.procurement_method = 2

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'
    # Onsite Field -N.GARA
    # Onsite Comment -also take notice_no from notice url
    

    try:
        notice_data.notice_no = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'p.regular-14.ng-binding'))).text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -BANDO
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#page-complete  div > p > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
   

    # Onsite Field -SCADE IL
    # Onsite Comment -None

    try: 
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, "div.stato.nopadding.noBorderElenco.text-center.col-sm-2 > div > div").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline1)
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ATTIVO DAL
    # Onsite Comment -None

    try: 
        publish_date1 = tender_html_element.find_element(By.CSS_SELECTOR, "div.stato.borderElenco.nopadding.col-sm-2").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date1)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#page-complete div > p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        button_close = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.close')))
        page_details.execute_script("arguments[0].click();",button_close)
    except:
        pass
    
    try:
        cookie_accept = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#cookie_accept.col-xs-4.col-xs-offset-4.col-sm-2.col-lg-1.col-sm-offset-0.btn.colorButtonWhite.bottom10-xs')))
        page_details.execute_script("arguments[0].click();",cookie_accept)
    except:
        pass
    
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div"
    # Onsite Comment -None
    try:
        notice_data.notice_text += WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#page-complete'))).get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
     
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.titoloiniziativa.col-sm-9.col-xs-12 > h2	').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -BANDO
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Consip S.p.A.'
        customer_details_data.org_parent_id = '6848985'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -there are multiple CPV basically there are various pages for CPV >>> " li.pagination-next.ng-scope > a" take data from each page # Onsite Comment -None
# Onsite Comment -None
#     notice_data.cpv_at_source = 'CPV' 
    try:
        cpv_at_source = ''
        category = ''
        for single_record in WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button.btn.colorButtonWhite.fontBlue.ng-scope'))):
            time.sleep(3)
            CPV_clk = single_record.click()
            time.sleep(5)
            for cpv_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.modal.fade.ng-scope.ng-isolate-scope.in > div > div > div > div:nth-child(3) > div'):
                cpvs_data = cpvs()
                cpv_code1 = cpv_record.text
                cpv_code = re.findall('\d{8}',cpv_code1)[0]
                cpvs_data.cpv_code = cpv_code
                cpv_at_source += cpv_code
                cpv_at_source += ','
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
                try:
                    category += cpv_record.find_element(By.CSS_SELECTOR, 'div.col-sm-8.nopadding.ng-binding').text.replace("Descrizione",'')
                    category += ','
                except Exception as e:
                    logging.info("Exception in category: {}".format(type(e).__name__))
                    pass

            CPV_close = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div/div/div[1]/div[2]')))
            page_details.execute_script("arguments[0].click();",CPV_close)
            time.sleep(3)
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.category = category.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        no_of_lots = page_details.find_elements(By.XPATH, "//div[contains(@data-ng-click, 'openDettaglio')]")
        no_of_lots_length = len(no_of_lots)
        for single_lottam in range(0,no_of_lots_length):
            each_lot_click = page_details.find_elements(By.XPATH, "//div[contains(@data-ng-click, 'openDettaglio')]//following::a")[single_lottam]
            page_details.execute_script("arguments[0].click();",each_lot_click)
            time.sleep(2)

            lot_rows = WebDriverWait(page_details, 160).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div#categorie.col-sm-12.nopadding.ng-scope')))
            lot_length = len(lot_rows)
            lot_number = 1
            for records in range(0,lot_length):
                each_lot = WebDriverWait(page_details, 160).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div#categorie.col-sm-12.nopadding.ng-scope')))[records]
                lot_details_data = lot_details()
                lot_details_data.lot_class_codes_at_source = 'CPV'
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = each_lot.text.split('\n')[0]
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                lot_cpv_at_source = ''
                time.sleep(3)
                CPV_clk = each_lot.find_element(By.CSS_SELECTOR, 'button.btn.colorButtonWhite.fontBlue.ng-scope')
                page_details.execute_script("arguments[0].click();",CPV_clk)
                time.sleep(5)
                for cpv_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.modal.fade.ng-scope.ng-isolate-scope.in > div > div > div > div:nth-child(3) > div'):
                    lot_cpvs_data = lot_cpvs()
                    cpv_code1 = cpv_record.text
                    cpv_code = re.findall('\d{8}',cpv_code1)[0]
                    lot_cpvs_data.lot_cpv_code = cpv_code

                    lot_cpv_at_source += cpv_code
                    lot_cpv_at_source += ','
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)

                lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                notice_data.cpv_at_source += ','+lot_details_data.lot_cpv_at_source
                lot_number +=1
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        DOCUMENTAZIONE_clk  = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"DOCUMENTAZIONE PER L'ABILITAZIONE")))
        page_details.execute_script("arguments[0].click();",DOCUMENTAZIONE_clk)
    except:
        pass

    try:
        
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sm-11.col-xs-12.margin-top-10-xs.text-center-xs.vertical-align-inside-div-text-left.nopadding.ellipsis'):
            attachments_data = attachments()
        # Onsite Field -take data from both the clicks"DOCUMENTAZIONE PER L'ABILITAZIONE" and "ALTRA DOCUMENTAZIONE"
        # Onsite Comment -ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=37dd9fd748a8b854"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
        
        # Onsite Field -take data from both the clicks"DOCUMENTAZIONE PER L'ABILITAZIONE" and "ALTRA DOCUMENTAZIONE"
        # Onsite Comment -ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=37dd9fd748a8b854"

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            
        # Onsite Field -take data from both the clicks"DOCUMENTAZIONE PER L'ABILITAZIONE" and "ALTRA DOCUMENTAZIONE"
        # Onsite Comment -ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=37dd9fd748a8b854"

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div').text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        ALTRA_DOCUMENTAZIONE_clk  = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"ALTRA DOCUMENTAZIONE")))
        page_details.execute_script("arguments[0].click();",ALTRA_DOCUMENTAZIONE_clk)
    except:
        pass

    try:
        
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sm-9.col-xs-12.margin-top-10-xs.text-center-xs.vertical-align-inside-div-text-left.nopadding.ellipsis'):
            attachments_data = attachments()
        # Onsite Field -take data from both the clicks"DOCUMENTAZIONE PER L'ABILITAZIONE" and "ALTRA DOCUMENTAZIONE"
        # Onsite Comment -ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=37dd9fd748a8b854"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
        # Onsite Field -take data from both the clicks"DOCUMENTAZIONE PER L'ABILITAZIONE" and "ALTRA DOCUMENTAZIONE"
        # Onsite Comment -ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=37dd9fd748a8b854"

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        # Onsite Field -take data from both the clicks"DOCUMENTAZIONE PER L'ABILITAZIONE" and "ALTRA DOCUMENTAZIONE"
        # Onsite Comment -ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=37dd9fd748a8b854"

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div').text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=AB#!/%23post_call_position#post_call_position"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[8]/div[5]/div[5]/div/div[1]/div[6]/div[2]/div/div[5]/div[1]/input')))
        page_main.execute_script("arguments[0].click();",clk)
        
        try:
            pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'select#paginazione.form-control.pagStyle.ng-pristine.ng-valid.ng-not-empty.ng-touched'))
            pp_btn.select_by_index(2)
        except:
            pass
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.listVetrina.col-sm-12.nopadding.ng-scope.borderSD'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.listVetrina.col-sm-12.nopadding.ng-scope.borderSD')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.listVetrina.col-sm-12.nopadding.ng-scope.borderSD')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[1]/div[3]/ul/li[4]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.listVetrina.col-sm-12.nopadding.ng-scope.borderSD'),page_check))
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
    
