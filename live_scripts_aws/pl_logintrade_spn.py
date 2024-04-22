from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pl_logintrade_spn"
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
from selenium.webdriver.chrome.options import Options 

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pl_logintrade_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'pl_logintrade_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
 
    notice_data.currency = 'PLN'
 
    notice_data.main_language = 'PL'
 
    notice_data.procurement_method = 2
 
    notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.blue-header').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Comment -Notice_no teke from notice_url..........Note:notice_no:"https://ciech.logintrade.net/zapytania_email,1547951,a4566fcd82fc69bfb58790efc2744d78.html" here take "a4566fcd82fc69bfb58790efc2744d78" in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.label').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data publikacji:
    # Onsite Comment -Note:Splite after "Data publikacji:" this keyword......Grab time also

    try:
        published_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2) > div.date").text
        publish_time = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2) > div.time").text
        publish_date = published_date + ' ' + publish_time
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data złożenia oferty:
    # Onsite Comment -Note:Splite after "Data złożenia oferty:" this keyword..... Grab time also

    try:
        deadline_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3) > div.date").text
        deadline_time = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3) > div.time").text
        notice_deadline = deadline_date + ' ' + deadline_time
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.company').text

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.blue-header > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,100)
        logging.info(notice_data.notice_url)
        
        try:
            WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'(//h1)[3]'))).text
        except:
            try:
                WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.title'))).text
            except:
                WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="infoPanel"]/a'))).text
        
        try:
            page_details_check = page_details.find_element(By.XPATH, '//*[@id="infoPanel"]/a').text
            if page_details_check !="":
                return
        except Exception as e:
            logging.info("Exception in page_details_check: {}".format(type(e).__name__))
            pass
    
        
        

#***************************************************FORMAT 1****************************************************************
        try:
            # Format 1 = https://ciech.logintrade.net/zapytania_email,1547951,a4566fcd82fc69bfb58790efc2744d78.html
            logging.info("Format 1")
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#container').get_attribute("outerHTML")

            try:  
                local_description1 = page_details.find_element(By.CSS_SELECTOR, '#aukcja2 > div:nth-child(15)').text
                local_description2 = page_details.find_element(By.CSS_SELECTOR, '#aukcja2 > div:nth-child(13) > div').text
                local_description = local_description1+' '+local_description2
                notice_data.local_description = local_description
                length = len(local_description)
                if length >= 5000:
                    first_part = local_description[:4900]
                    notice_summary_first_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                    second_part = local_description[4900:]
                    notice_summary_second_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                    notice_data.notice_summary_english = notice_summary_first_part+' '+notice_summary_second_part
                else:
                    notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except:
                try:
                    local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiry contents")]//following::div[1]').text
                    notice_data.local_description = local_description
                    length = len(local_description)
                    if length >= 5000:
                        first_part = local_description[:4900]
                        notice_summary_first_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                        second_part = local_description[4900:]
                        notice_summary_second_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                        notice_data.notice_summary_english = notice_summary_first_part+' '+notice_summary_second_part
                    else:
                        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                except:
                    try:
                        local_description = page_details.find_element(By.CSS_SELECTOR, '#aukcja2 > div:nth-child(14)').text
                        notice_data.local_description = local_description
                        length = len(local_description)
                        if length >= 5000:
                            first_part = local_description[:4900]
                            notice_summary_first_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                            second_part = local_description[4900:]
                            notice_summary_second_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                            notice_data.notice_summary_english = notice_summary_first_part+' '+notice_summary_second_part
                        else:
                            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                    except Exception as e:
                        logging.info("Exception in local_description1: {}".format(type(e).__name__))
                        pass
                
            # Onsite Comment -Note:Click on "div:nth-child(3) a" this button "Show contact detail" on page_detail than grab the data
            # Ref_url=https://zepak.logintrade.net/zapytania_email,1548762,8b0c7b01cda6807dfd3069d7baf24d43.html

            try: 
                customer_details_data = customer_details()
                customer_details_data.org_country = 'PL'
                customer_details_data.org_language = 'PL'

                customer_details_data.org_name = org_name
                # Onsite Comment -Note:Add "#firma_info > h3:nth-child(3)" both selector
                try:
                    org_address = page_details.find_element(By.CSS_SELECTOR, '#firma_info').text.split('\n')[1:3]
                    customer_details_data.org_address = ','.join(org_address) 
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass
                
                try:
                    contact_details_click = WebDriverWait(page_details, 60).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="pokaz_dane_kontaktowe"]')))
                    page_details.execute_script("arguments[0].click();",contact_details_click)
                    time.sleep(3)

                    # Onsite Field -Purchaser
                    # Onsite Comment -Note:Split between "Purchaser:" and "Phone:"
                    try:
                        customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Purchaser:")]//following::h3[1]').text
                    except Exception as e:
                        logging.info("Exception in contact_person: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Phone:
                    # Onsite Comment -Note:Splite after "Phone:" this keyword

                    try:
                        org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone:")]//parent::h3|(//*[contains(text(),"tel")])[1]').text
                        if "tel" in org_phone:
                            customer_details_data.org_phone = org_phone.split('tel.')[1].split(',')[0].strip()
                        elif 'Phone:' in org_phone:
                             customer_details_data.org_phone = org_phone.split('Phone:')[1].strip()
                    except Exception as e:
                        logging.info("Exception in org_phone: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -e-mail:
                    # Onsite Comment -Note:Splite after "e-mail:" this keyword

                    try:
                        customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"e-mail:")]//parent::h3').text.split('e-mail:')[1].strip()
                    except Exception as e:
                        logging.info("Exception in org_email: {}".format(type(e).__name__))
                        pass
                except:
                    try:
                        # Onsite Field -Purchaser
                        # Onsite Comment -Note:Split between "Purchaser:" and "Phone:"
                        try:
                            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Purchaser:")]//following::h3[1]').text
                        except Exception as e:
                            logging.info("Exception in contact_person: {}".format(type(e).__name__))
                            pass

                        # Onsite Field -Phone:
                        # Onsite Comment -Note:Splite after "Phone:" this keyword

                        try:
                            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone:")]//parent::h3|(//*[contains(text(),"tel")])[1]').text
                            if "tel" in org_phone:
                                customer_details_data.org_phone = org_phone.split('tel.')[1].split(',')[0].strip()
                            elif 'Phone:' in org_phone:
                                customer_details_data.org_phone = org_phone.split('Phone:')[1].strip()
                        except Exception as e:
                            logging.info("Exception in org_phone: {}".format(type(e).__name__))
                            pass

                        # Onsite Field -e-mail:
                        # Onsite Comment -Note:Splite after "e-mail:" this keyword

                        try:
                            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"e-mail:")]//parent::h3').text.split('e-mail:')[1].strip()
                        except Exception as e:
                            logging.info("Exception in org_email: {}".format(type(e).__name__))
                            pass
                    except:
                        pass
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass
            
            # Ref_url= https://zepak.logintrade.net/zapytania_email,1548232,22b1802feb0cb5e9da6460f167b75222.html
            try:  
                lot_number = 1
                for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Products:")]//following::table[1]/tbody/tr')[1:]:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number
                # Onsite Field -Products: >> Index

                    try:
                        lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                        if lot_actual_number == '-':
                            lot_details_data.lot_actual_number = lot_actual_number.replace('-','').strip()
                        else:
                            lot_details_data.lot_actual_number = lot_actual_number
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass

                # Onsite Field -Products: >> Product name

                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                # Onsite Field -Products: >> Quantity

                    try:
                        lot_details_data.lot_quantity = float(single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text)
                    except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass

                # Onsite Field -Products: >> Unit

                    try:
                        lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    except Exception as e:
                        logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                        pass

            #         # Ref_url= https://hutabankowa.logintrade.net/zapytania_email,1547941,4d643b7d2d5d191859daf2ffc10693c4.html
                    try:
                        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Offer evaluation criteria")]//following::ol[1]/li'):
                            lot_criteria_data = lot_criteria()

                            # Onsite Field -Offer evaluation criteria
                            # Onsite Comment -Note:"Price - 85%" here grab only "Price"

                            lot_criteria_data.lot_criteria_title = single_record.text.split('-')[0].strip()

                            lot_criteria_data.lot_criteria_weight = int(single_record.text.split('-')[1].split('%')[0].strip())
                            
                            lot_criteria_data.lot_criteria_cleanup()
                            lot_details_data.lot_criteria.append(lot_criteria_data)
                    except Exception as e:
                        logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                        pass

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number +=1 
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass
            
            # Onsite Field -Attachments:
            # Ref_url= https://ciech.logintrade.net/zapytania_email,1547951,a4566fcd82fc69bfb58790efc2744d78.html
            try:              
                for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Attachments:")]//following::ul/li'):
                    attachments_data = attachments()

                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'p').text.split('.')[0].strip()
                    try:
                        attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'p').text.split('.')[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'em').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
                pass
            
#*************************************************FORMAT 2****************************************************************
        except:
            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainPageContent').get_attribute("outerHTML")
                
                # Format 2 = https://cobra-europe.logintrade.net/portal,szczegolyZapytaniaOfertowe,aa3376cafd1b0a83a8672daddf60b580.html
                logging.info("Format 2")
                try:
                    local_description = page_details.find_element(By.CSS_SELECTOR, '#sectionContent > div:nth-child(1) > div.dataField.infoHeader').text
                    notice_data.local_description = local_description
                    length = len(local_description)
                    if length >= 5000:
                        first_part = local_description[:4900]
                        notice_summary_first_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                        second_part = local_description[4900:]
                        notice_summary_second_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                        notice_data.notice_summary_english = notice_summary_first_part+' '+notice_summary_second_part
                    else:
                        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                except:
                    try:
                        local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiry contents")]//following::div[1]').text
                        notice_data.local_description = local_description
                        length = len(local_description)
                        if length >= 5000:
                            first_part = local_description[:4900]
                            notice_summary_first_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                            second_part = local_description[4900:]
                            notice_summary_second_part = GoogleTranslator(source='auto', target='en').translate(first_part)
                            notice_data.notice_summary_english = notice_summary_first_part+' '+notice_summary_second_part
                        else:
                            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                    except Exception as e:
                        logging.info("Exception in local_description2: {}".format(type(e).__name__))
                        pass

                    
                try:              
                    customer_details_data = customer_details()
                    customer_details_data.org_country = 'PL'
                    customer_details_data.org_language = 'PL'

                    customer_details_data.org_name = org_name
                    # Onsite Comment -Note:Add "#buyerInfo > div:nth-child(3)" both selector

                    try:
                        org_address = page_details.find_element(By.CSS_SELECTOR, '#buyerInfo').text.split('\n')[1:3]
                        customer_details_data.org_address = ','.join(org_address)
                    except Exception as e:
                        logging.info("Exception in org_address: {}".format(type(e).__name__))
                        pass

                    # Onsite Comment -Note:Splite after "Buyer:" this keyword

                    try:
                        customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '#buyerContact > div:nth-child(1)').text.split(':')[1].strip()
                    except Exception as e:
                        logging.info("Exception in contact_person: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -landline

                    try:
                        try:
                            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#buyerContact > div:nth-child(2)').text.split('telefon stacjonarny: -')[1].strip()
                        except:
                            try:
                                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone:")]//parent::h3|(//*[contains(text(),"tel")])[1]').text
                                if "tel" in org_phone:
                                    customer_details_data.org_phone = org_phone.split('tel.')[1].split(', ')[0].strip()
                                elif 'Phone:' in org_phone:
                                     customer_details_data.org_phone = org_phone.split('Phone:')[1].strip()
                            except:
                                pass
                            
                    except Exception as e:
                        logging.info("Exception in org_phone: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -e-mail

                    try:
                        customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#buyerContact > div:nth-child(4)').text.split('e-mail:')[1]
                    except Exception as e:
                        logging.info("Exception in org_email: {}".format(type(e).__name__))
                        pass

                    customer_details_data.customer_details_cleanup()
                    notice_data.customer_details.append(customer_details_data)
                except Exception as e:
                    logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                    pass
                
                try:
                    description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]/..').text
                    if description !="":
                        lot_data = []
                        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Products")]//following::table[1]//tr')[1::2]:
                                lot_title = single_record.text
                                lot_data.append(lot_title)


                        lot_description_data = []  
                        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Products")]//following::table[1]//tr')[2::2]:
                            lot_description = single_record.find_element(By.CSS_SELECTOR, 'div.info').text
                            lot_description_data.append(lot_description)

                        lot_number = 1
                        for title,description in zip(lot_data,lot_description_data):
                            lot_details_data = lot_details()
                            lot_details_data.lot_number = lot_number

                            try:
                                lot_quantity = title.split(' ')[-2].strip()
                                lot_details_data.lot_quantity = float(lot_quantity)
                            except Exception as e:
                                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                                pass

                            try:
                                lot_details_data.lot_quantity_uom = title.split(' ')[-1].strip()
                            except Exception as e:
                                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                                pass

                            lot_details_data.lot_title = title.split('.')[1].split(lot_quantity)[0].strip()

                            try:
                                lot_details_data.lot_description = description.split('Description:')[1].strip()
                            except:
                                pass

                            try:
                                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#sectionCriteria > div.infoField > div.field'):
                                    lot_criteria_data = lot_criteria()

                                    lot_criteria_data.lot_criteria_title = single_record.text.split('-')[0].split('.')[1].strip()

                                    lot_criteria_weight = single_record.text.split('-')[1].split('%')[0].strip()
                                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)

                                    lot_criteria_data.lot_criteria_cleanup()
                                    lot_details_data.lot_criteria.append(lot_criteria_data)
                            except Exception as e:
                                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                                pass

                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number += 1
                except:
                    try:
                        lot_number = 1
                        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Products")]//following::table[1]//tr')[1:]:
                            lot_details_data = lot_details()
                            lot_details_data.lot_number = lot_number

                        # Onsite Field -Products >> Product

                            try:
                                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td.index').text
                            except Exception as e:
                                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                                pass


                            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td.product.full').text
                            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)


                        # Onsite Field -Products >> Quantity

                            try:
                                lot_details_data.lot_quantity = float(single_record.find_element(By.CSS_SELECTOR, 'td.quantity').text)
                            except Exception as e:
                                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                                pass

                # Onsite Field -Products >> Unit

                            try:
                                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td.units').text
                            except Exception as e:
                                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                                pass

                            try:
                                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                                lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_lc) 
                                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                            except Exception as e:
                                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                                pass

                    # Ref_url=https://hutabankowa.logintrade.net/zapytania_email,1547941,4d643b7d2d5d191859daf2ffc10693c4.html
                            try:
                                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#sectionCriteria > div.infoField > div.field'):
                                    lot_criteria_data = lot_criteria()

                                    # Onsite Field -Offer evaluation criteria
                                    # Onsite Comment -Note:"Price - 85%" here grab only "Price"

                                    lot_criteria_data.lot_criteria_title = single_record.text.split('-')[0].split('.')[1].strip()

                                    lot_criteria_weight = single_record.text.split('-')[1].split('%')[0].strip()
                                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)

                                    lot_criteria_data.lot_criteria_cleanup()
                                    lot_details_data.lot_criteria.append(lot_criteria_data)
                            except Exception as e:
                                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                                pass

                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number += 1
                    except Exception as e:
                        logging.info("Exception in lot_details_data: {}".format(type(e).__name__)) 
                        pass
                    
                try:              
                    for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Attachments")]//following::table[1]/tbody[1]/tr')[1:]:
                        attachments_data = attachments()

                        attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text.split('.')[0].strip()
                        try:
                            attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text.split('.')[-1].strip()
                        except Exception as e:
                            logging.info("Exception in file_type: {}".format(type(e).__name__))
                            pass

                        try:
                            attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                        except Exception as e:
                            logging.info("Exception in file_size: {}".format(type(e).__name__))
                            pass

                        attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > a').get_attribute('href')

                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
                except Exception as e:
                    logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
                    pass
                
                try:              
                    for single_record in page_details.find_elements(By.CSS_SELECTOR, '#productsList > tbody > tr> td > div > div > div > a'):
                        attachments_data = attachments()

                        attachments_data.file_name = single_record.text.split('.')[0].strip()
                
                        try:
                            attachments_data.file_type = single_record.text.split('.')[-1].split(' ')[0].strip()
                        except Exception as e:
                            logging.info("Exception in file_type: {}".format(type(e).__name__))
                            pass

                        attachments_data.external_url = single_record.get_attribute('href')

                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
                except Exception as e:
                    logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
                    pass

            except:
                notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in load_page: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://platformazakupowa.logintrade.pl/"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,50):#50
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="offers-table"]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="offers-table"]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="offers-table"]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="offers-table"]/table/tbody/tr'),page_check))
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
