from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sa_nupco_ca"
log_config.log(SCRIPT_NAME)
import re,time
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download_nupco as Doc_Download
from gec_common.web_application_properties import *
import nupco_script as ns
import pandas as pd
import pdfplumber
title_head = ['LONG TEXT','ITEM DESCRIPTION','MATERIAL DESCRIPTION','NUPCO DESCRIPTION','NUPCO Description',
                  'ITEM SPECIFICATION','Short Description','Description','DESCRIPTION','Long Item Description',
                  'MATERIAL DESCRIPTION','FINAL LONG TEXT','ITEM LONG DESCRIPTION','MATERIAL LONG DESCRIPTION',
                  'LONG DESC','SHORT TEXT','Item Description','ITEM NAME','Item Description ']

quantity_head = ['Quantity','INITIAL QUANTITY','QUANTITY','Initial Qty','Total QTY','QTY','Final QUANTITY','Final Total QTY','Total','MODA INITIAL QTY','Final Quantities','Nedded QTY']

lot_quantity_uom_head = ['UOM','SRM UOM','OUM','UNIT','UOM2','Unit']

lot_actual_number_head = ['SRM CODE','NUPCO CODE','SRM Code','NUPCO Code','NUPCO CODE2',' Item Code ','Product']

bidder_name_head = ['VENDOR NAME','Vendor Name']

bidder_country_head = ['COUNTRY','Country']

award_quantity_head = ['Final Quantity','Final Quantities','Quantitiy','Final Quantity ة!ئاهنلا تا!مᝣلا']

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sa_nupco_ca"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'sa_nupco_ca'
    notice_data.main_language = 'AR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SA'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'SAR'
    notice_data.procurement_method = 2
    
    notice_type = tender_html_element.find_element(By.CSS_SELECTOR,'p.box_arbic_text_p').text
    if 'النتائج النهائية' in notice_type:
        notice_data.notice_type = 7
    else:
        return
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box.box_arbic  div.box_arbic_col01').text.split("رقم المنافسة")[1].replace('\n','')
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > p:nth-child(2)').text  
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        cpvs_data = cpvs()
        cpvs_data.cpv_code = '33000000'
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    notice_data.cpv_at_source = '33000000'
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.column-box.mix div > a').get_attribute("href") 
        logging.info(notice_data.notice_url)                    
    except:
        notice_data.notice_url = url
        
    try:
        fn.load_page(page_details,notice_data.notice_url,180)
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.right.paddingright').get_attribute("outerHTML")                     
    except Exception as e:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML") 
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    
    notice_data.publish_date = threshold
    
    try:
        document_opening_time = page_details.find_element(By.CSS_SELECTOR, 'div.right.paddingright > div:nth-child(3) > p').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
    except:
        try:
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m-%d-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
                pass
    
    try:
        notice_data.document_fee = page_details.find_element(By.CSS_SELECTOR, 'div.right.paddingright > div:nth-child(4) > p').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'NATIONAL UNIFIED PROCUREMENT COMPANY (NUPCO)'
        customer_details_data.org_parent_id = 7700088
        customer_details_data.org_address = 'Saeed Al Salami Street,DigitalCity Riyadh 12251 – 2721Kingdom of Saudi Arabia'
        customer_details_data.org_phone = '+920018184 966'
        customer_details_data.org_country='SA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.btn_wrap_Tender > ul > li:nth-child(n)'):
            external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            try:
                if 'xlsx' in external_url or 'pdf' in external_url or 'PDF' in external_url or 'doc' in external_url or 'xml' in external_url or 'xmls' in external_url:
                    attachments_data = attachments()
                    file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
                    attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(file_name) 
                    attachments_data.file_description = attachments_data.file_name 
                    page_details.get(external_url)
                    time.sleep(5)
    #                 external_url = single_record.find_element(By.CSS_SELECTOR, 'a').click()
                    file_dwn = Doc_Download.file_download()
                    attachments_data.external_url = str(file_dwn[0])

                    try:
                        attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('.')[-1]
                    except Exception as e:
                        logging.info("Exception in external_url: {}".format(type(e).__name__))
                        pass
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
                    folderpath = attachments_data.external_url.split('/sa_nupco')[1]
                    pdfpath = NOTICE_ATTACHEMENTS_DIR +'/sa_nupco' + folderpath
                    list_of_dict = []
                    if attachments_data.file_name == 'The final results' and 'pdf' in attachments_data.external_url:
                        csv_file_path = pdfpath.replace('pdf','csv')
                        ns.main(pdfpath,csv_file_path)
                        time.sleep(2)
                        list_of_dict = fn.nupco_csv(csv_file_path)
                        with pdfplumber.open(pdfpath) as pdf:
                            for i in pdf.pages[:1]:
                                pdftext = i.extract_text()
                                try:
                                    publish_date = re.findall('\w+ \d+, \d{4}',pdftext)[0]
                                    notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                                except:
                                    try:
                                        publish_date = re.findall('\d+-\w+-\d{4}',pdftext)[0]
                                        notice_data.publish_date = datetime.strptime(publish_date,'%d-%B-%Y').strftime('%Y/%m/%d %H:%M:%S')
                                    except:
                                        pass
                                logging.info(notice_data.publish_date)
                    elif attachments_data.file_name == 'The final results' and 'xlsx' in attachments_data.external_url:
                        df = pd.read_excel(pdfpath)
                        list_of_dict = df.to_dict('records')
                    lot_number = 1
                    for lot in list_of_dict:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        try:
                            lot_cpvs_data = lot_cpvs()
                            lot_cpvs_data.lot_cpv_code = '33000000'
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        except Exception as e:
                            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                            pass
                        lot_details_data.lot_cpv_at_source = '33000000'
                        for actual_number in lot_actual_number_head:
                            try:
                                lot_details_data.lot_actual_number = lot[actual_number].replace('\n',' ')
                            except:
                                pass

                        try:
                            lot_details_data.lot_description = lot['Long Description'].replace('\n',' ')
                        except:
                            try:
                                lot_details_data.lot_description = lot['LONG TEXT'].replace('\n',' ')
                            except:
                                pass  

                        for t in title_head:
                            try:
                                lot_details_data.lot_title = lot[t].replace('\n',' ')
                            except:
                                pass

                        for quantity_uom in lot_quantity_uom_head:
                            try:
                                lot_details_data.lot_quantity_uom = lot[quantity_uom].replace('\n',' ')
                            except:
                                pass

                        for lotquantity in quantity_head:
                            try:
                                lot_details_data.lot_quantity = float(lot[lotquantity])
                            except:
                                pass

                        try:
                            lot_details_data.contract_duration = lot['Contract Period'].replace('\n',' ')
                        except:
                            try:
                                lot_details_data.contract_duration = lot['CONTRACT PERIOD'].replace('\n',' ')
                            except:
                                pass

                        try:
                            award_details_data = award_details()
                            for biddername in bidder_name_head:
                                try:
                                    award_details_data.bidder_name = lot[biddername].replace('\n',' ')
                                    if 'Cancel' in award_details_data.bidder_name or 'CANCEL' in award_details_data.bidder_name:
                                        lot_details_data.lot_is_canceled = True
                                except:
                                    pass

                            for awardquantity in award_quantity_head:
                                try:
                                    award_details_data.award_quantity = float(lot[awardquantity])
                                except:
                                    pass

                            try:
                                award_details_data.grossawardvaluelc = float(lot['TOTAL PRICE'].replace(',','').strip())
                            except:
                                pass
                            if award_details_data.bidder_name != None and award_details_data.bidder_name != '':
                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)
                        except:
                            pass
                        if lot_details_data.lot_title != None and lot_details_data.lot_title != '':
                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number += 1
                else:
                    attachments_data = attachments()
                    file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
                    attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(file_name) 
                    logging.info(attachments_data.file_name)
                    if attachments_data.file_name != 'Buy competition':
                        attachments_data.file_description = attachments_data.file_name 
                        attachments_data.external_url = external_url
                        logging.info(attachments_data.external_url)
                        try:
                            attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('.')[-1]
                        except Exception as e:
                            logging.info("Exception in external_url: {}".format(type(e).__name__))
                            pass
                        if attachments_data.external_url != '':
                            attachments_data.attachments_cleanup()
                            notice_data.attachments.append(attachments_data)
            except:
                attachments_data = attachments()
                file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
                attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(file_name) 
                logging.info(attachments_data.file_name)
                if attachments_data.file_name != 'Buy competition':
                    attachments_data.file_description = attachments_data.file_name 
                    attachments_data.external_url = external_url
                    logging.info(attachments_data.external_url)
                    try:
                        attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('.')[-1]
                    except Exception as e:
                        logging.info("Exception in external_url: {}".format(type(e).__name__))
                        pass
                    if attachments_data.external_url != '':
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://nupco.com/%d8%a7%d9%84%d9%85%d9%86%d8%a7%d9%81%d8%b3%d8%a7%d8%aa/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Container"]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Container"]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
        except:
            logging.info("No new record")
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    logging.info("Exception:"+str(e))
    raise e
    
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
