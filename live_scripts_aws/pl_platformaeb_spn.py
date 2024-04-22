from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pl_platformaeb_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download_ingate
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "pl_platformaeb_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()

    notice_data.script_name = 'pl_platformaeb_spn'
    notice_data.main_language = 'PL'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'PLN'
    notice_data.notice_type = 4
    notice_data.procurement_method = 2

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of purchase order
    # Onsite Comment -Replace following keywords with given respective keywords ('Service =Service', 'Construction work  = Works' , 'Delivery = Supply')

    try:
        contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(13)').text
        if contract_type_actual == " ":
            pass
        else:
            notice_data.contract_type_actual = contract_type_actual
            
        if "Service" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Construction work" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Delivery" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Awarding procedure status
    # Onsite Comment -None

    try: 
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(15)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Creation date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(20)").text
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Stage closing date:
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(17)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    try:
        fn.load_page(page_details,notice_data.notice_url,100)
        logging.info(notice_data.notice_url)
        
        
        WebDriverWait(page_details, 100).until(EC.presence_of_element_located((By.XPATH,'//*[contains(text(),"General information")]'))).text

        
        try:
            only_num = notice_data.notice_url.split('.html/')[1].split('/')[0].strip()
        except:
            pass

        try:
            notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        except:
            pass

        try:
            notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if notice_no !="" and notice_no != ' ':
                notice_data.notice_no = notice_no
            else:
                notice_data.notice_no = only_num
        except:
            pass
        
        try:
            clk_popup = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="button-1014-btnEl"]'))).click()
            time.sleep(5)
        except:
            pass
    
        # Onsite Field -None
        # Onsite Comment -there are two tabs available to grab data as follows 1)Awarding procedure settings  2)Sponsor's attachments
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@class="x-body x-webkit x-chrome x-reset"]').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'PL'
            customer_details_data.org_language = 'PL'
        # Onsite Field -Sponsor's company
        # Onsite Comment -None

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text

        # Onsite Field -Ordering party
        # Onsite Comment -None

            try:
                org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
                if org_address == " ":
                    pass
                else:
                    customer_details_data.org_address = org_address
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

        # Onsite Field -Awarding procedure status
        # Onsite Comment -None

            try:
                org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
                if org_city ==" ":
                    pass
                else:
                    customer_details_data.org_city = org_city
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '''//*[contains(text(),"Sponsor's company:")]//following::td/a[1]''').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                phone1 = page_details.find_element(By.XPATH, '''//*[contains(text(),"Sponsor's company:")]//following::td[1]''').text.split('\n')[2].split('\n')[0].strip()
                phone = re.sub("[^\d]", "", phone1)
                customer_details_data.org_phone = phone
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
    
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description of awarding procedure:")]/..').text.split("Description of awarding procedure:")[1].strip()
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
# Onsite Field -Awarding procedure item >> Description of an awarding procedure item and evaluation criteria
# Onsite Comment -None
        try:
            for plus_clk in page_details.find_elements(By.CSS_SELECTOR, 'div.x-grid-row-expander'):
                plus_clk.click()
                time.sleep(5)
        except:
            pass

        try:
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.x-grid-group-title'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

            # Onsite Field -Awarding procedure item description
            # Onsite Comment -click on "+" button to open lot details,  ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/422649/zapytanie-o-cene-rfq-na-modernizacje-systemu-kontroli-dostepu-skd-wraz-z-wizualizacja-zdarzen-systemu-kontroli-dostepu-oraz-systemu-sygnalizacji-pozaru-ssp"

                lot_details_data.lot_title = single_record.text.split(".")[1].split(":")[0]
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                try:
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except:
                    pass

            # Onsite Field -Quantity
            # Onsite Comment -click on "+" button to open lot details,  ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/422649/zapytanie-o-cene-rfq-na-modernizacje-systemu-kontroli-dostepu-skd-wraz-z-wizualizacja-zdarzen-systemu-kontroli-dostepu-oraz-systemu-sygnalizacji-pozaru-ssp"

                try:
                    lot_quantity = single_record.text.split(lot_details_data.lot_title)[1]
                    try:
                        lot_quantity = re.findall("\d+ \d+",lot_quantity)[0]
                    except:
                        lot_quantity = re.findall("\d+",lot_quantity)[0]
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Unit
            # Onsite Comment -click on "+" button to open lot details,  ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/422649/zapytanie-o-cene-rfq-na-modernizacje-systemu-kontroli-dostepu-skd-wraz-z-wizualizacja-zdarzen-systemu-kontroli-dostepu-oraz-systemu-sygnalizacji-pozaru-ssp"

                try:
                    lot_quantity_uom = single_record.text.split(lot_quantity)[-1].replace(".",'').strip()
                    if len(lot_quantity_uom) > 20:
                        lot_quantity_uom = re.findall("\d+.\w+",lot_quantity_uom)[-1]
                        lot_details_data.lot_quantity_uom = lot_quantity_uom.split(' ')[1].strip()
                    else:
                        lot_details_data.lot_quantity_uom =lot_quantity_uom 
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass


        try:
            clk_attachments = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Sponsor's attachments")])[1]''').click()
            time.sleep(2)
        except:
            pass  

        try:
            Download_dropdown = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Download files")])[1]''').click()
            time.sleep(2)
        except:
            pass
    
        try:              

            # Onsite Field -Attachments to publication  # (//*[contains(text(),"Download all sponsor's attachments")])[2]  # //*[contains(text(),'Download selected attachments')]//following::a[1]   # a#menuitem-1086-itemEl.x-menu-item-link
            # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.  # //*[contains(text(),'Download selected attachments')]//following::a[1]
            external_url = page_details.find_element(By.XPATH, '''//*[contains(text(),'Download selected attachments')]//following::a[1]''').click()
            time.sleep(10)
            try:
                data = page_details.find_element(By.XPATH, '''//*[@id="messagebox-1001-displayfield-inputEl"]''').text
                if "To gain access to attachments, you have to apply for participation in the awarding procedure." in data or 'No attachments found for download.'in data:
                    pass
                else: 
                    ok_clk = page_details.find_element(By.XPATH, '''//*[@id="button-1005-btnInnerEl"]''').click()
                    time.sleep(2) 
                    for single_record in page_details.find_elements(By.CSS_SELECTOR, '''div.x-grid-row-checker'''):
                        try:
                            clk_box = single_record.click()
                            time.sleep(5)
                        except:
                            pass  
                        
                        download_clk = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Download")])[1]''').click()
                        time.sleep(2)
                        try:
                            attachments_data = attachments()
                            file_dwn = Doc_Download.file_download()
                            attachments_data.external_url= (str(file_dwn[0]))

                            if attachments_data.external_url != '':
                                attachments_data.file_name = "Sponsor's attachments"
                                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()


                            attachments_data.attachments_cleanup()
                            notice_data.attachments.append(attachments_data)
                        except:
                            data = page_details.find_element(By.XPATH, '''//*[@id="messagebox-1001-displayfield-inputEl"]''').text
                            if "Przekroczono dozwolony limit pobierania plików w krótkim czasie. Aby pobrać plik spróbuj ponownie później po:" in data or 'No attachments found for download.'in data:
                                ok_clk = page_details.find_element(By.XPATH, '''//*[@id="button-1005-btnInnerEl"]''').click()
                                time.sleep(2)
                                pass
                        try:
                            unclk_box = single_record.click()
                            time.sleep(5)
                        except:
                            pass 
                        
            except:
                attachments_data = attachments()
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url= (str(file_dwn[0]))

                if attachments_data.external_url != '':
                    attachments_data.file_name = "Sponsor's attachments"
                    attachments_data.file_type = "zip"

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    
    except Exception as e:
        logging.info("Exception in load_page: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = Doc_Download.page_details
page_details.maximize_window()


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://platforma.eb2b.com.pl/open-auctions.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        try:
            clk_popup = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="button-1014-btnEl"]'))).click()
            time.sleep(2)
        except:
            pass

        try:
            for page_no in range(1,5):#5
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    if notice_count == 5:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'(//button[@class="x-btn-center"])[4]/span')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr[2]'),page_check))
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
