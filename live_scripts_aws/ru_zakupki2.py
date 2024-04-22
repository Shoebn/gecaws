from gec_common import log_config
SCRIPT_NAME = "ru_zakupki"
log_config.log(SCRIPT_NAME)
import shutil
from bs4 import BeautifulSoup
from gec_common.gecclass import *
import logging
import re,os,sys
import jsons
from datetime import date, datetime, timedelta
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.web_application_properties as application_properties


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
output_json_folder = "jsonfile"
SCRIPT_NAME = "ru_zakupki"
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-ru-en")
model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-ru-en")
tnotice_count = 0
notice_count = 0

days = 1
tofld = 10
fromfld = 20



def russian_translator(text):
    input_ids = tokenizer.encode(text, return_tensors="pt")
    outputs = model.generate(input_ids)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return result
th = date.today()- timedelta(int(days))
threshold = th.strftime('%Y%m%d')

output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
extract_path = application_properties.TMP_DIR + "/zakupki_extract_file/"  + threshold + '/'
page_detail = fn.init_chrome_driver()

try:
    xml_folder_name = os.listdir(extract_path)
    for xml_folder in xml_folder_name[int(tofld):int(fromfld)]:
        xml_folder = extract_path + xml_folder
        if 'notification_' in xml_folder:
            xml_files_name = os.listdir(xml_folder)
            for xml_file in xml_files_name:
                xml_file = xml_folder +'/'+ xml_file
                if ('.xml' in  xml_file):
                    with open(xml_file, 'r', encoding='UTF-8') as f:
                        soup = BeautifulSoup(f, "xml")
                        notice_data = tender()
                        notice_data.script_name = "ru_zakupki_spn"
                        notice_data.main_language = 'RU'
                        notice_data.procurement_method = 2
                        notice_data.currency='RUB'
                        
                        performance_country_data = performance_country()
                        performance_country_data.performance_country = 'RU'
                        notice_data.performance_country.append(performance_country_data)
                        notice_data.document_type_description = 'Извещение о проведении электронного аукциона'
                        notice_data.notice_type = 4
                        
                        try:
                            versionNumber = soup.export.find("versionNumber").text
                            if '1' not in versionNumber:
                                notice_data.notice_type = 16
                        except:
                            pass
                        try:
                            publish_date = soup.export.find("plannedPublishDate").text
                            publish_date = re.findall('\d{4}-\d+-\d+', publish_date)[0]
                            notice_data.publish_date = datetime.strptime(publish_date, '%Y-%m-%d').strftime('%Y/%m/%d')
                            logging.info(notice_data.publish_date)                            
                        except:
                            pass
                        
                        try:
                            notice_data.notice_no = soup.export.find("purchaseNumber").text
                            notice_data.notice_url = 'https://zakupki.gov.ru/epz/order/notice/printForm/view.html?regNumber='+notice_data.notice_no
                            # fn.load_page(page_detail,notice_data.notice_url)
                            notice_data.notice_text = str(soup)
                        except:
                            pass
                        
                        try:
                            notice_data.contract_duration = soup.export.find("term").text
                        except:
                            pass
                        
                        try:
                            notice_data.additional_tender_url = soup.export.find('url').text
                        except:
                            pass
                        
                        try:
                            category = soup.export.epNotificationEF2020.notificationInfo.OKPD2.find("OKPDCode").text
                        except:
                            pass
                        try:
                            notice_data.local_title = soup.export.find("purchaseObjectInfo").text
                            notice_data.notice_title = russian_translator(notice_data.local_title)
                            logging.info(notice_data.notice_title)
                        except:
                            pass
                        
                        try:
                            notice_deadline = soup.export.find("endDT").text
                            notice_deadline = re.findall('\d{4}-\d+-\d+', notice_deadline)[0]
                            notice_data.notice_deadline = datetime.strptime(notice_deadline, '%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass
                        
                        try:
                            notice_data.est_amount = float(soup.export.find("maxPrice").text)
                            notice_data.grossbudgetlc = notice_data.est_amount
                        except:
                            pass
                        
                        try:
                            customer_details_data = customer_details()
                            try:
                                customer_details_data.org_name = soup.export.find("fullName").text
                            except:
                                pass
                            try:
                                customer_details_data.org_address = soup.export.find("factAddress").text
                            except:
                                pass
                            try:
                                customer_details_data.org_email = soup.export.find("contactEMail").text.rstrip('.')
                                if ';' in customer_details_data.org_email:
                                    customer_details_data.org_email = customer_details_data.org_email.split(';')[0].strip()
                                if '/' in customer_details_data.org_email:
                                    customer_details_data.org_email = customer_details_data.org_email.split('/')[0].strip()
                            except:
                                pass
                            try:
                                customer_details_data.org_phone = soup.export.find("contactPhone").text
                            except:
                                pass
                            try:
                                customer_details_data.org_fax = soup.export.find('contactFax').text
                            except:
                                pass
                            try:
                                lastName = soup.export.find("lastName").text
                                firstName = soup.export.find("firstName").text
                                middleName = soup.export.find("middleName").text
                                customer_details_data.contact_person = lastName +' '+ firstName +' '+ middleName
                            except:
                                pass
                            customer_details_data.org_country = 'RU'
                            customer_details_data.org_language = 'RU'
                            customer_details_data.customer_details_cleanup()
                            notice_data.customer_details.append(customer_details_data)
                        except:
                            pass
                        
                        try:              
                            for single_record in soup.export.find_all("attachmentInfo"):
                                attachments_data = attachments()
                                attachments_data.file_size = single_record.find('fileSize').text
                                attachments_data.file_name = single_record.find('fileName').text.split('.')[0]
                                attachments_data.file_description = single_record.find('docDescription').text
                                attachments_data.file_type = single_record.find('fileName').text.split('.')[-1].strip()
                                attachments_data.external_url = single_record.find('url').text
                                attachments_data.attachments_cleanup()
                                notice_data.attachments.append(attachments_data)
                        except:
                            pass
                        
                        try:
                            lot_number = 1
                            for single_record in soup.export.find_all("purchaseObject"):
                                lot_details_data = lot_details()
                                lot_details_data.lot_title = single_record.find('name').text
                                if notice_data.local_title is None:
                                    notice_data.local_title = lot_details_data.lot_title
                                if notice_data.notice_title is None:
                                    notice_data.notice_title = lot_details_data.lot_title
                                lot_details_data.lot_title_english = russian_translator(lot_details_data.lot_title)
                                try:
                                    lot_details_data.lot_actual_number = single_record.find('code').text
                                except:
                                    try:
                                        lot_details_data.lot_actual_number = single_record.find('OKPDCode').text
                                    except:
                                        pass                                    
                                try:
                                    lot_description = ''
                                    for singlerecord in soup.export.find_all('characteristicsUsingReferenceInfo'):
                                        lot_description += singlerecord.find('name').text
                                        lot_description += '\n'
                                    lot_details_data.lot_description = lot_description
                                except:
                                    pass
                                try:
                                    lot_details_data.lot_quantity_uom = single_record.find('type').text
                                except:
                                    pass
                                try:
                                    lot_details_data.lot_quantity = float(single_record.find('quantity').text)
                                except:
                                    pass
                                try:
                                    lot_details_data.lot_grossbudget_lc = float(single_record.find('price').text)
                                except:
                                    pass
                                lot_details_data.lot_number = lot_number
                                lot_details_data.lot_details_cleanup()
                                notice_data.lot_details.append(lot_details_data)
                                lot_number += 1
                        except Exception as e:
                            logging.info("Exception in lot_details: {}".format(type(e).__name__))
                            pass
                        notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
                        logging.info(notice_data.identifier)
                        logging.info('----------------------------------')       
                        notice_data.tender_cleanup()
                        output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
                        notice_count += 1
                        tnotice_count += 1
                        if notice_count == 50:
                            output_json_file.copyFinalJSONToServer(output_json_folder)
                            output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                            notice_count = 0
                    os.remove(xml_file)
        elif 'requestquotation_' in xml_folder:
            xml_files_name = os.listdir(xml_folder)
            for xml_file in xml_files_name:
                xml_file = xml_folder +'/'+ xml_file
                if ('.xml' in  xml_file):
                    with open(xml_file, 'r', encoding='UTF-8') as f:
                        soup = BeautifulSoup(f, "xml")
                        notice_data = tender()
                        notice_data.script_name = "ru_zakupki_spn"
                        notice_data.main_language = 'RU'
                        notice_data.procurement_method = 2
                        notice_data.currency='RUB'
                        notice_data.document_type_description = 'Извещение о проведении электронного аукциона'
                        notice_data.additional_tender_url = 'url'
                        performance_country_data = performance_country()
                        performance_country_data.performance_country = 'RU'
                        notice_data.performance_country.append(performance_country_data)
                        
                        notice_data.notice_type = 4
                        
                        try:
                            versionNumber = soup.export.find("versionNumber").text
                            if '01' not in versionNumber:
                                notice_data.notice_type = 16
                        except:
                            pass
                        try:
                            publish_date = soup.export.find("docPublishDate").text
                            publish_date = re.findall('\d{4}-\d+-\d+', publish_date)[0]
                            notice_data.publish_date = datetime.strptime(publish_date, '%Y-%m-%d').strftime('%Y/%m/%d')
                        except:
                            pass
                        try:
                            notice_data.notice_no = soup.export.find("id").text
                            notice_data.notice_url = 'https://zakupki.gov.ru/epz/pricereq/printForm/view.html?priceRequestInfoId='+notice_data.notice_no
                            # fn.load_page(page_detail,notice_data.notice_url)
                            notice_data.notice_text = str(soup)
                        except:
                            pass
                        try:
                            category = soup.export.find("code").text
                        except:
                            pass
                        
                        try:
                            notice_data.contract_duration = soup.export.find("term").text
                        except:
                            pass
                        
                        try:
                            notice_data.local_title = soup.export.find("requestObjectInfo").text
                            notice_data.notice_title = russian_translator(notice_data.local_title)
                            logging.info(notice_data.notice_title)
                        except:
                            pass
                        
                        try:
                            notice_deadline = soup.export.find("endDate").text
                            notice_deadline = re.findall('\d{4}-\d+-\d+', notice_deadline)[0]
                            notice_data.notice_deadline = datetime.strptime(notice_deadline, '%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass
                        
                        try:
                            customer_details_data = customer_details()
                            try:
                                customer_details_data.org_name = soup.export.find("fullName").text
                            except:
                                pass
                            try:
                                customer_details_data.org_address = soup.export.find("factAddress").text
                            except:
                                pass
                            try:
                                customer_details_data.org_email = soup.export.find("contactEMail").text.rstrip('.')
                                if ';' in customer_details_data.org_email:
                                    customer_details_data.org_email = customer_details_data.org_email.split(';')[0].strip()
                            except:
                                pass
                            try:
                                customer_details_data.org_phone = soup.export.find("contactPhone").text
                            except:
                                pass
                            
                            try:
                                customer_details_data.org_fax = soup.export.find('contactFax').text
                            except:
                                pass

                            try:
                                lastName = soup.export.find("lastName").text
                                firstName = soup.export.find("firstName").text
                                middleName = soup.export.find("middleName").text
                                customer_details_data.contact_person = lastName +' '+ firstName +' '+ middleName
                            except:
                                pass
                            customer_details_data.org_country = 'RU'
                            customer_details_data.org_language = 'RU'
                            customer_details_data.customer_details_cleanup()
                            notice_data.customer_details.append(customer_details_data)
                        except:
                            pass
                        
                        try:
                            lot_number = 1
                            for single_record in soup.export.find_all("product"):
                                lot_details_data = lot_details()
                                lot_details_data.lot_title = single_record.find('name').text
                                if notice_data.local_title is None:
                                    notice_data.local_title = lot_details_data.lot_title
                                if notice_data.notice_title is None:
                                    notice_data.notice_title = lot_details_data.lot_title
                                
                                lot_details_data.lot_title_english = russian_translator(lot_details_data.lot_title)
                                try:
                                    lot_details_data.lot_actual_number = single_record.find('code').text
                                except:
                                    try:
                                        lot_details_data.lot_actual_number = single_record.find('OKPDCode').text
                                    except:
                                        pass
                                try:
                                    lot_details_data.lot_quantity = float(single_record.find('quantity').text)
                                except:
                                    pass
                                lot_details_data.lot_number = lot_number
                                lot_details_data.lot_details_cleanup()
                                notice_data.lot_details.append(lot_details_data)
                                lot_number += 1
                        except Exception as e:
                            logging.info("Exception in lot_details: {}".format(type(e).__name__))
                            pass
                        notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
                        logging.info(notice_data.identifier)
                        logging.info('----------------------------------')       
                        notice_data.tender_cleanup()
                        output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
                        notice_count += 1
                        tnotice_count += 1
                        if notice_count == 50:
                            output_json_file.copyFinalJSONToServer(output_json_folder)
                            output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                            notice_count = 0
                    os.remove(xml_file)
        shutil.rmtree(xml_folder)
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_detail.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
