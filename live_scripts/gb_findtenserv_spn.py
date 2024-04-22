from gec_common.gecclass import *
import logging
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "gb_findtenserv_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'gb_findtenserv_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'GBP'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2 > a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    try:
        fn.load_page(page_details, notice_data.notice_url, 80)
        logging.info(notice_data.notice_url)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "(//*[contains(text(),'Name and addresses')])[2]"))).text
        notice_data.class_at_source = 'CPV'
        
        try:
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text

            cpv_code = cpv_code.split('-')[0].strip()

            cpvs_data = cpvs()

            cpvs_data.cpv_code = cpv_code
            notice_data.cpv_at_source = cpv_code+','
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        try:
            text1 = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text

            cpv1  =fn.get_string_between(text1,'II.2.2) Additional CPV code(s)','II.2.3) Place of performance')

            cpv_regex1 = re.compile(r'\d{8}')

            lot_cpvs_dataa1 = cpv_regex1.findall(cpv1)

            for cpv in lot_cpvs_dataa1:

                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv

                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

                notice_data.cpv_at_source += cpv
                notice_data.cpv_at_source += ','

            notice_data.cpv_at_source = notice_data.cpv_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__))
            pass

        try:
            notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > dd').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'div.search-result-header > h2').text
            notice_data.notice_title = notice_data.local_title
            if len(notice_data.notice_title) < 5:
                notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text.split(' - ')[1]

        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > dd").text
            try:
                notice_deadline = re.findall('\d+ \w+ \d{4}, \d+:\d+[apAP][mM]', notice_deadline )[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline ,'%d %B %Y, %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_deadline = re.findall('\d+ \w+ \d{4}', notice_deadline )[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline ,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')

            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH,'//*[contains(text(),"VI.3) Additional information")]//following::a[1]').text
            notice_data.additional_tender_url =notice_data.additional_tender_url.split('"')[0]
        except:
            try:
                notice_data.additional_tender_url = page_details.find_element(By.XPATH,'//*[contains(text(),"Buyer")]//following::p[1]').text
            except:
                pass

        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH,'//*[contains(text(),"Reference number")]//following::p[1]').text
        except:
            try:
                related_tender_id = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text
                notice_data.related_tender_id = related_tender_id.split('(MT Ref:')[1].split(')')[0]
            except:
                pass


        if 'Lot No' not in page_details.find_element(By.CSS_SELECTOR, 'div#main-content').text:
            try:
                notice_data.tender_contract_start_date = page_details.find_element(By.XPATH,'//*[contains(text(),"Start date")]//following::p[1]').text
                notice_data.tender_contract_start_date = datetime.strptime(notice_data.tender_contract_start_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass

            try:
                notice_data.tender_contract_end_date = page_details.find_element(By.XPATH,'//*[contains(text(),"End date")]//following::p[1]').text
                notice_data.tender_contract_end_date = datetime.strptime(notice_data.tender_contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass

        try:
            notice_data.contract_duration = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text.split('Duration in months\n')[1].split('\n')[0]
            notice_data.contract_duration = 'Duration in months:  ' + notice_data.contract_duration
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR,'div.govuk-width-container > main').get_attribute("outerHTML")
        except Exception as e:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass

        try:
            lot_deatils = page_details.find_element(By.CSS_SELECTOR, 'div#main-content').text.split('II.2) Description')
            lot_number = 1
            for lot in lot_deatils:
                if 'Lot No' in lot:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

                    lot_actual_number = lot.split("Lot No\n")[1].split('\n')[0]
                    lot_details_data.lot_actual_number = lot_actual_number 

                    lot_details_data.lot_title = lot.split("Title\n")[1].split('\n')[0]
                    if len(lot_details_data.lot_title) == 6:
                        lot_details_data.lot_title =  lot_details_data.lot_actual_number
                    try:
                        lot_details_data.lot_description = lot.split('Description of the procurement\n')[1].split('II.2.5')[0]
                        lot_details_data.lot_description_english = lot_details_data.lot_description 
                    except Exception as e:
                        logging.info("Exception in lot_description: {}".format(type(e).__name__))
                        pass
                    try:
                        lot_netbudget_lc = lot.split('Estimated value')[1].split('Value excluding VAT: £')[1].split('\n')[0]
                        lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(',', ''))
                    except Exception as e:
                        logging.info("Exception in lot_netbudgetlc: {}".format(type(e).__name__))
                        pass

                    if lot_details_data.lot_actual_number in lot_actual_number: 
                        try:
                            lot_details_data.contract_start_date = lot.split('Start date')[1].split('\n')[1].split('\n')[0]
                            lot_details_data.contract_start_date = datetime.strptime(lot_details_data.contract_start_date, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass
                        try:
                            lot_details_data.contract_end_date = lot.split('End date')[1].split('\n')[1].split('\n')[0]
                            lot_details_data.contract_end_date = datetime.strptime(lot_details_data.contract_end_date, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass

                    if 'Main site or place of performance' in lot:
                        try:
                            lot_details_data.lot_nuts = lot.split('NUTS codes')[1].split('Main site or place of performance')[0]
                            lot_details_data.lot_nuts = lot_details_data.lot_nuts.splitlines()
                            lot_details_data.lot_nuts = ','.join(lot_details_data.lot_nuts)
                            lot_details_data.lot_nuts  = lot_details_data.lot_nuts.lstrip(',')
                        except Exception as e:
                            logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                            pass
                    else:
                        try:
                            lot_details_data.lot_nuts = lot.split('NUTS codes\n')[1].split('\n')[0]
                        except:
                            try:
                                lot_details_data.lot_nuts = page_details.find_element(By.XPATH,'//*[contains(text(),"NUTS codes")]//following::ul[1]').text
                            except Exception as e:
                                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                                pass

                    try:
                        lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p[1]').text
                        if 'Services' in lot_details_data.lot_contract_type_actual :
                             lot_details_data.contract_type = 'Service'
                        elif 'Works' in lot_details_data.lot_contract_type_actual :
                             lot_details_data.contract_type = 'Works'
                        elif 'Works' in lot_details_data.lot_contract_type_actual :
                            lot_details_data.contract_type = 'Supply'
                        else:
                            pass
                    except Exception as e:
                        logging.info("Exception in contract_type: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_details_data.contract_duration = lot.split('Duration in months\n')[1].split('\n')[0]
                        lot_details_data.contract_duration = 'Duration in months:  ' + lot_details_data.contract_duration
                    except Exception as e:
                        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                        pass

                    try:
                        cpv = fn.get_string_between(lot, 'II.2.2) Additional CPV code(s)', 'II.2.3) Place of performance')
                        cpv_regex = re.compile(r'\d{8}')
                        lot_cpvs_dataa = cpv_regex.findall(cpv)
                        for cpv in lot_cpvs_dataa:
                            lot_cpvs_data = lot_cpvs()
                            lot_cpvs_data.lot_cpv_code = cpv
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    except Exception as e:
                        logging.info("Exception in lot_cpv: {}".format(type(e).__name__))
                        pass

                    try:
                        cpv = fn.get_string_between(lot, 'II.2.2) Additional CPV code(s)', 'II.2.3) Place of performance')
                        cpv_regex = re.compile(r'\d{8}')
                        lot_cpvs_dataa = cpv_regex.findall(cpv)
                        lot_cpv_at_source = ''
                        for cpv in lot_cpvs_dataa:
                            lot_cpv_at_source += cpv
                            lot_cpv_at_source += ','
                        lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                    except Exception as e:
                        logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                        pass
                    
                    try:
                        for l in lot.split('\n'):
                            if 'criterion ' in l or 'Weighting' in l or 'Price' in l:
                                lot_criteria_data = lot_criteria()
                                if 'price' in l.lower():
                                     lot_criteria_data.lot_criteria_title = 'Price'
                                else:

                                    lot_criteria_data.lot_criteria_title = l.split('- Name:')[1].split('/')[0]

                                lot_criteria_weight = (l.split('Weighting:'))[1]
                                if '%' in lot_criteria_weight:
                                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight.split('%')[0])
                                else:
                                    lot_criteria_data.lot_criteria_weight = int(l.split('Weighting:')[1])
                                lot_criteria_data.lot_criteria_cleanup()
                                lot_details_data.lot_criteria.append(lot_criteria_data)
                    except Exception as e:
                        logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                        pass


                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1


        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass
        
        lot_deatils = page_details.find_element(By.CSS_SELECTOR, 'div#main-content').text
        if 'Lot No' not in lot_deatils:
            try:
                try:
                    local_description1 = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text
                    if "Short description" in local_description1 and "II.1.5)" in local_description1:
                        local_description1 = local_description1.split('Short description\n')[1].split('II.1.5)')[0].strip()
                    else:
                        local_description1 = local_description1.split('Short description\n')[1].split('II.1.6)')[0].strip()
                except:
                    pass

                try:
                    local_description2 = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text
                    if "Description of the procurement" in local_description2 and "II.2.5)" in local_description2:
                        local_description2 = local_description2.split('Description of the procurement\n')[1].split('II.2.5)')[0]
                    else:
                        local_description2 = local_description2.split('Description of the procurement\n')[1].split('II.2.7)')[0]
                except:
                    pass
                local_description  = f"{local_description1} {local_description2}"
                notice_data.local_description  = local_description.replace('\n','').replace('\n','')
                notice_data.notice_summary_english = notice_data.local_description 
            except:
                pass
        else:
            try:
                try:
                    local_description1 = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text
                    if "Short description" in local_description1 and "II.1.5)" in local_description1:
                        local_description1 = local_description1.split('Short description')[1].split('II.1.5)')[0].strip()
                    else:
                        local_description1 = local_description1.split('Short description')[1].split('II.1.6)')[0].strip()
                except:
                    pass
                    
                notice_data.local_description  = local_description1
                notice_data.notice_summary_english = notice_data.local_description 
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass
        
        try:
            tender_cri = page_details.find_element(By.CSS_SELECTOR, 'div#main-content').text
            if 'Lot No' not in tender_cri:
                a=tender_cri.split('II.2.5) Award criteria')[1]
                for l in a.split('\n'):

                    try:
                        if 'criterion ' in l or 'Weighting' in l or 'price' in l.lower():  
                            tender_criteria_data = tender_criteria()


                            if 'price' in l.lower():
                                 tender_criteria_data.tender_criteria_title = 'Price'
                            else:
                                tender_criteria_data.tender_criteria_title = l.split('- Name:')[1].split('/')[0]  


                            tender_criteria_weight = l.split('Weighting: ')[1].strip()
                            if '%' in tender_criteria_weight:                   
                                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight.split('%')[0])
                            else:
                                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)


                            if tender_criteria_data.tender_criteria_weight > 0:
                                tender_criteria_data.tender_criteria_cleanup()
                                notice_data.tender_criteria.append(tender_criteria_data)          
                    except:
                        pass
        except:
            pass

        try:
            notice_data.notice_no = page_details.find_element(By.XPATH,'//*[contains(text(),"Notice reference")]//parent::p[1]').text.split('Notice reference:')[1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            publish_date = page_details.find_element(By.CSS_SELECTOR, "div.govuk-grid-column-three-quarters.break-word").text.split('Published ')[1]
            publish_date = re.findall('\d+ \w+ \d{4}, \d+:\d+[apAP][mM]', publish_date)[0]

            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y, %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)

        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p').text
            if 'Services' in notice_data.contract_type_actual:
                 notice_data.notice_contract_type = 'Service'
            elif 'Works' in notice_data.contract_type_actual:
                 notice_data.notice_contract_type = 'Works'
            elif 'Supplies' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply'
            else:
                pass
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:
            netbudgetlc = page_details.find_element(By.XPATH,'//*[contains(text(),"Estimated total value")]//following::p[1]').text
            notice_data.netbudgetlc = netbudgetlc.split('Value excluding VAT:')[1].split(' £')[1]
            notice_data.netbudgetlc  = float(notice_data.netbudgetlc.replace(',', '').strip()) 
        except:
            try:
                netbudgetlc = page_details.find_element(By.XPATH,'//*[contains(text(),"Estimated value")]//following::p[1]').text
                notice_data.netbudgetlc = netbudgetlc.split('Value excluding VAT: ')[1].split(' £')[1]
                notice_data.netbudgetlc  = float(notice_data.netbudgetlc.replace(',', '').strip()) 
            except Exception as e:  
                logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
                pass

        try:
            notice_data.est_amount = notice_data.netbudgetlc
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass

        try:
            try:
                notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH,'//*[contains(text(),"Type of procedure")]//following::p[1]').text
            except:
                 notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH,'//*[contains(text(),"Form of procedure")]//following::p[1]').text
            notice_data.type_of_procedure = fn.procedure_mapping("assets/uk_findtenserv_procedure.csv",notice_data.type_of_procedure_actual)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

        try:
            source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Information about European Union Funds")]//following::p[1]').text
            if 'Yes' in source_of_funds:
                notice_data.source_of_funds = 'International agencies'
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agency = 1344862
                notice_data.funding_agencies.append(funding_agencies_data)
        except Exception as e:
            logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data = customer_details()
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR,'div.search-result-sub-header.wrap-text').text
            try:
                org_address_2 = page_details.find_element(By.XPATH,'//*[contains(text(),"Name and addresses")]//following::p[2]').text
                org_address_3 = page_details.find_element(By.XPATH,'//*[contains(text(),"Name and addresses")]//following::p[3]').text
                org_address_4 = page_details.find_element(By.XPATH,'//*[contains(text(),"Name and addresses")]//following::p[4]').text
                customer_details_data.org_address = f"{org_address_2} {org_address_3} {org_address_4}"
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text.split('Main activity')[1].split('Section II: Object')[0]
            except:
                pass

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text.split('Type of the contracting authority')[1].split('I.5) ')[0]
            except:
                pass

            try:
                contact_person = page_details.find_element(By.XPATH,'//*[contains(text(),"Contact")]//following::p[1]').text
                if len(contact_person) < 23:
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH,'//*[contains(text(),"Telephone")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                org_email = page_details.find_element(By.XPATH, '//h4[text()="Email"]//following::p[1]').text
                if '@' in org_email:
                    customer_details_data.org_email = org_email
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH,'//*[contains(text(),"NUTS code")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH,'//*[contains(text(),"Internet address(es)")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'GB'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__))
            pass

        try:
            cpvs_data = cpvs()
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text
            cpvs_data.cpv_code = cpv_code.split('-')[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        try:
            attachments_data = attachments()

            try:
                attachments_data.file_size = page_details.find_element(By.XPATH,'//*[contains(text(),"Download")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.external_url = page_details.find_element(By.XPATH,'//*[contains(text(),"Download")]//following::a[1]').get_attribute('href')
            try:
                if 'PDF' in attachments_data.external_url:
                    attachments_data.file_type = 'PDF'
                    attachments_data.file_name = 'Download'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__))
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.notice_type) + str(notice_data.notice_url)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')


# ----------------------------------------- Main Body
arguments = ['--incognito', 'ignore-certificate-errors', 'allow-insecure-localhost', '--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.find-tender.service.gov.uk/Search/Results']
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            click_1 = page_main.find_element(By.XPATH, "//input[contains(@name,'stage[4]')]").click()
            time.sleep(3)
        except:
            pass
        try:
            click_2 = page_main.find_element(By.XPATH, "//input[contains(@name,'stage[3]')]").click()
            time.sleep(3)
        except:
            pass
        try:
             click_2 = page_main.find_element(By.XPATH, "//input[contains(@name,'stage[1]')]").click()
        except:
            pass
        try:
            click_3 = page_main.find_element(By.XPATH, "//button[contains(@class,'govuk-button form-control')]").click()
            time.sleep(3)
        except:
            pass

        try:
            for page_no in range(1,50):#50
                page_check = WebDriverWait(page_main, 50).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div[1]'))).text
                rows = WebDriverWait(page_main, 60).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))
                length = len(rows)
    
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(
                        EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:
                    next_page = WebDriverWait(page_main, 50).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.standard-paginate-next.govuk-link.break-word')))
                    page_main.execute_script("arguments[0].click();", next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(
                        EC.text_to_be_present_in_element((By.XPATH, '//*[@id="listTemplate"]/table/tbody/tr'), page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
