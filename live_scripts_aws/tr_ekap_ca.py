from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tr_ekap_ca"
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
from selenium.webdriver.support.select import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tr_ekap_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Note : URL is not changable

# for Explore CA details              1) first Go to URL : "https://ekap.kik.gov.tr/EKAP/Ortak/IhaleArama/index.html"

#                                     2) Go to "Tender Status" Drop down (left side of page ) and select 2 options for CA 
#                                                               option 1 : Contract Signed 
#                                                               option 2 : Results Announcement Published

#                                     3)    click on "filter" button for view details ----------(located in left upper side)                                     
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'tr_ekap_ca'
    
    notice_data.main_language = 'TR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -Sözleşme Bilgileri
    # Onsite Comment -click on "Bilgiler" option (selector : li:nth-child(1) > button ), after that you will see 5 tabs , then select "Sözleşme Bilgileri"(selector :  #ulTabs > li:nth-child(5)> a)  and get the data from "Sözleşme Bilgileri" field, [for ex. "3.650.000,00 TRY", here split only "TRY" ]
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -split the data from tender_html_page
    
    notice_data.notice_url = url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text> h6').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.card-text').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -İhale Onay Tarihi
    # Onsite Comment -click on "Bilgiler" option (selector : li:nth-child(1) > button ) for page main and select "İhale Bilgileri"(selector: #ulTabs > li.active ) tab for publish_date

    try:
        publish_date = page_main.find_element(By.CSS_SELECTOR, 'p.alt.text-muted').text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass 
    
    # Onsite Field -"Sözleşme İmzalanmış"  , "Sonuç İlanı Yayımlanmış"
    # Onsite Comment -take document_type_description "Sözleşme İmzalanmış"  when "Tender Status" is "Contract Signed" and take document_type_description "Sonuç İlanı Yayımlanmış"  when "Tender Status" is "Results Announcement Published"

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div > span').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type. for eg. "Mal - 4734 / 3-g / Diğer Sözleşme İmzalanmış" , take only "Mal" in notice_contract_type.   2.replace following keyword with given keywords ("Hizmet=Service" , "Mal=Supply", "Danışmanlık=Consultancy" , "Yapım=Works" )

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div').text.split('-')[0].strip()
        if 'Hizmet' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Mal' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Danışmanlık' in notice_contract_type:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'Yapım' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split type_of_procedure_actual. for eg."Mal - 4734 / 3-g / Açık Sözleşme İmzalanmış" , here  take only "Açık" in type_of_procedure_actual.

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.card-text > div").text.split('-')[1].split('\n')[0].strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/tr_ekap_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'TR'
        customer_details_data.org_language = 'TR'
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-5 p').text
        # Onsite Field -None
        # Onsite Comment -split only city, for ex. "ANKARA - 20.09.2023 11:00", here split only "ANKARA"

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.alt.text-muted').text.split("-")[0].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            clk = WebDriverWait(tender_html_element, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.col-md-5 li:nth-child(1)'))).click()
            iframe = page_main.find_element(By.XPATH,'//*[@id="sonuclar"]/div/div/div[2]/iframe')
            page_main.switch_to.frame(iframe)
            time.sleep(5)
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' #ucBirBakistaIhale_Label19')))
        except:
            pass
        
         # Onsite Field -İhale Yeri - Tarihi - Saati
        # Onsite Comment -click on "Bilgiler" option (selector : li:nth-child(1) > button ),  in the first tab i.e("İhale Bilgileri")  you will see "İhale Yeri - Tarihi - Saati" field, split only address, for ex. "Samsun 19 Mayıs Polis Meslek Yüksek Okulu Brifing Salonu - 04.10.2023 10:00", here split only "Samsun 19 Mayıs Polis Meslek Yüksek Okulu Brifing Salonu"

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Yeri")]//following::span[1]').text.split("-")[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Bilgiler
    # Onsite Comment -click on "Bilgiler" option (selector : li:nth-child(1) > button ) , you will be see the 5 tabs ("İhale Bilgileri" , "İdare Bilgileri" , "İşlemler" , "İlan Bilgileri" , " Sözleşme Bilgileri")
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#tabIhaleBilgi > div > table > tbody').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        cpvs_code = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Branş Kodları (OKAS)")]//following::td[1]').text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number= 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        lot_details_data.contract_type = notice_data.notice_contract_type
    
        # Onsite Field -Bilgiler
        # Onsite Comment -when you click on "Bilgiler" option (selector : li:nth-child(1) > button ), main page will open , you can see "cpvs" in "İhale Bilgileri"(selector : #ulTabs > li.active ) tab
        
        try:
            cpvs_code = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Branş Kodları (OKAS)")]//following::td[1]').text
            cpv_regex = re.compile(r'\d{8}')
            cpvs_data = cpv_regex.findall(cpvs_code)
            for cpv in cpvs_data:
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = cpv
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass
        # Onsite Field -Sözleşme Bilgileri
        # Onsite Comment -for award details click on "Bilgiler" option (selector : li:nth-child(1) > button ), you will see 5 tabs, then  select last tab i.e " Sözleşme Bilgileri"(selector: #ulTabs > li:nth-child(5)> a), to view award details
        
        try:
            clk=  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ulTabs > li:nth-child(5)> a'))).click()
            time.sleep(5)
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(7) > p > span.sozLabel > b')))
        except:
            pass

        award_details_data = award_details()

            # Onsite Field -None
            # Onsite Comment -for award details click on "Bilgiler" option (selector : li:nth-child(1) > button ), you will see 5 tabs, then  select last tab i.e " Sözleşme Bilgileri"(selector: #ulTabs > li:nth-child(5)> a), to view bidder_name

        award_details_data.bidder_name = page_main.find_element(By.CSS_SELECTOR, 'div.col-xs-12.col-sm-12 div > div.card-header').text

            # Onsite Field -Sözleşme Tarihi
            # Onsite Comment -for award details click on "Bilgiler" option (selector : li:nth-child(1) > button ), you will see 5 tabs, then select last tab i.e "Sözleşme Bilgileri"(selector: #ulTabs > li:nth-child(5)> a), to view award_date, split the data from "Sözleşme Tarihi"

        try:
            award_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Sözleşme Tarihi")]//following::span[1]').text
            award_date = re.findall('\d+.\d+.\d{4}',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%d.%m.%Y').strftime('%Y/%m/%d')
            lot_details_data.lot_award_date = award_details_data.award_date
        except:
            pass

            # Onsite Field -Sözleşme Bilgileri
            # Onsite Comment -for award details click on "Bilgiler" option (selector : li:nth-child(1) > button ), you will see 5 tabs, then select last tab i.e "Sözleşme Bilgileri"(selector: #ulTabs > li:nth-child(5)> a), to view GrossAwardValueLc, split the data from "Sözleşme Tarihi"  for ex."48.500.000,00 TRY", here split only "48.500.000,00"

        try:
            grossawardvaluelc = page_main.find_element(By.XPATH, '//*[contains(text(),"Sözleşme Bilgileri")]//following::span[4]').text
            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
            grossawardvaluelc =grossawardvaluelc.replace('.','')
            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','.').strip())
        except:
            pass

        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.currency = page_main.find_element(By.XPATH, '//*[contains(text(),"Sözleşme Bilgileri")]//following::span[4]').text.split(" ")[1]
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    
    try:
        page_main.switch_to.default_content()
        back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.card-footer.list-complete-item > button.close'))).click()
        time.sleep(2)
    except:
        pass
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.form-group.custom-controls-stacked.last-custom-controls-stacked')))
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.col-xs-12.col-sm-12.col-md-12.col-lg-12.sozlesmeCard > div > div.card-block').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ekap.kik.gov.tr/EKAP/Ortak/IhaleArama/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        index=["5","15"]
        for i in index:
            select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#autoScroll > div:nth-child(4) > select'))
            select_fr.select_by_value(i)

            try:
                clk=  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#pnlFiltreBtn > button')))
                page_main.execute_script("arguments[0].click();",clk)
                time.sleep(5)
            except:
                pass
            
            try:
                WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(1) > div > div > div > div.col-md-5 > div > div > ul > li:nth-child(1) > button > span')))
            except:
                pass

            try:
                rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="sonuclar"]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="sonuclar"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
            except:
                logging.info("No new record")
                pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
