#click on "Pesquisa avançada" next >>>  click on Anuncios(Adverts) from top left box>>> select dates "Data da publicação" >>> next click on "Pesquisar"

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pt_base_spn"
log_config.log(SCRIPT_NAME)
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
SCRIPT_NAME = "pt_base_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'pt_base_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PT'
    notice_data.performance_country.append(performance_country_data)
 
    notice_data.main_language = 'PT'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)>a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Nº do anúncio
    # Onsite Comment -None

    try:
        notice_no = page_details.find_element(By.XPATH, '''//*[contains(text(),'Nº do anúncio')]//following::td[1]''').text
        if notice_no == "-":
            pass
        else:
            notice_data.notice_no = notice_no
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[-1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Publicação
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
                                        
    try: 
        end_days_str = page_details.find_element(By.XPATH, '''//*[contains(text(),'Prazo para apresentação de propostas')]//following::td[1]''').text 
        if 'dias' in end_days_str:
            end_days = re.sub("[^\d]","",end_days_str)
            end_days_int = int(end_days)
            end_date = datetime.strptime(notice_data.publish_date,"%Y/%m/%d %H:%M:%S")
            days_after = (end_date + timedelta(days=end_days_int))
            notice_data.notice_deadline = days_after.strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objeto do contrato
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

      # Onsite Field -Tipo de procedimento
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/pt_base_spn_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    # Onsite Field -Prazo para apresentação de propostas
    # Onsite Comment -None
     # Onsite Field -Preço contratual
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '''//*[contains(text(),'Peças do procedimento')]//following::td[1]/a''').get_attribute("href")
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '''//*[contains(text(),'Descrição')]//following::td[1]''').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.b-body-screen > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'PT'
        customer_details_data.org_language = 'PT'
        
    # Onsite Field -Entidade
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -CPVs
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '''//*[contains(text(),'CPVs')]//following::td[1]''').text.split('-')[0].strip()
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass

    try:              
        cpvs_data = cpvs()
    # Onsite Field -CPVs
    # Onsite Comment -None

        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),'CPVs')]//following::td[1]''').text.split('-')[0].strip()

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -"Anúncio"
    # Onsite Comment -None
    try:              
        attachments_data = attachments()
    # Onsite Field -"Anúncio"
    # Onsite Comment -None

        attachments_data.file_name = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Anúncio')])[9]//following::a[1]''').text
        
        attachments_data.external_url = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Anúncio')])[9]//following::a[1]''').get_attribute('href')                   
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipos de contrato")]//following::td[1]').text
        notice_contract_type_en = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        if "Acquisition of services" in notice_contract_type_en or 'Concession of public services' in notice_contract_type_en:
            notice_data.notice_contract_type ="Service"
        elif "Acquisition of movable assets" in notice_contract_type_en or 'Leasing of movable assets' in notice_contract_type_en:
            notice_data.notice_contract_type ="Supply"
        elif "Public works concession" in notice_contract_type_en or 'Public works contracts' in notice_contract_type_en:
            notice_data.notice_contract_type ="Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # community.vortal
    
    try:
        lotts_attachments_url = page_details.find_element(By.XPATH, '''//*[contains(text(),'Peças do procedimento')]//following::td[1]/a''').get_attribute("href")                     
        if 'community.vortal' in lotts_attachments_url:
            fn.load_page(page_details1,lotts_attachments_url,80)
            
            try:
                notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#tblContainer > tbody').get_attribute("outerHTML")                     
            except:
                pass
            
            try:
                notice_data.related_tender_id = page_details1.find_element(By.XPATH,'''//*[contains(text(),'Request Reference:')]//following::td[1]''').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
            # title  div#Title.custom-form-item.questionTitleField.vInput
            
            try:
                lot_number = 1
                for single_record in page_details1.find_elements(By.CSS_SELECTOR,'div.SectionRowForPrint'): 
                    lot_details_data = lot_details()
                    lot_details_data.lot_number =lot_number  # div.ant-col.ant-col-9.gridCol
                    
                    try:
                        lot_netbudget = single_record.find_element(By.CSS_SELECTOR, 'div.ant-col.ant-col-5.gridCol > div  div:nth-child(2) span').text
                        lot_netbudget = re.sub("[^\d\.\,]","",lot_netbudget)
                        lot_details_data.lot_netbudget = float(lot_netbudget.replace(' ','').replace(',','.').strip())
                        lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
                    except Exception as e:
                        logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                        pass
                    
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div.ant-col.ant-col-9.gridCol div > div:nth-child(2)').text
                        
                    try:  
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type
                    except:
                        pass

                    try:
                        lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > span').text
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass
                    
                    try:
                        lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > span').text
                    except Exception as e:
                        logging.info("Exception in lot_description: {}".format(type(e).__name__))
                        pass

                # Onsite Field -Unit
                # Onsite Comment -None

                    try:
                        lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > div > span').text
                    except Exception as e:
                        logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > div > span').text
                        lot_quantity = re.sub("[^\d\.\,]","",lot_quantity)
                        lot_details_data.lot_quantity = float(lot_quantity.replace(',','').strip())
                    except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass
                    
    
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number +=1
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass

            try:              
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.ant-table-content > div > table > tbody > tr'):
                    tender_criteria_data = tender_criteria()

                    tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').text
                    if 'Preço' in tender_criteria_title:
                        tender_criteria_data.tender_criteria_title = 'price'
                        tender_criteria_data.tender_is_price_related = True

                        tender_criteria_weight =single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span').text.split('%')[0].strip()
                        tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)              

                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
            except Exception as e:
                logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
                pass

            try:
                for single_record in page_details1.find_elements(By.XPATH, '/html/body/div[2]/div/form/table/tbody/tr[4]/td/table/tbody/tr[18]/td/fieldset/div/table/tbody/tr[3]/td/div/table/tbody/tr')[2:]:
                    attachments_data = attachments()
                # Onsite Field -File Name
                # Onsite Comment -Note:Don't take file extention

                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[0].strip()
                    external = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute('onclick')
                    if "javascript:" in external:
                        external_url = re.findall('\d{8}',external)[0]
                        attachments_data.external_url = "https://community.vortal.biz/PRODPublic/Archive/RetrieveFile/Index?DocumentId="+str(external_url)+"&InCommunity=False&InPaymentGateway=False&DocUniqueIdentifier="                                    
                    else:
                        attachments_data.external_url = external                          

                    try:
                        attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass

                        # Onsite Field -Document Type
                    # Onsite Comment -None

                    try:
                        attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('.')[0].strip()
                    except Exception as e:
                        logging.info("Exception in file_description: {}".format(type(e).__name__))
                        pass           
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)

            except Exception as e:
                logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
                pass
            
            try:
                attachments_data = attachments()
                attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'div.ant-spin-nested-loading > div > span > div > a').get_attribute('href')
                attachments_data.file_type = page_details1.find_element(By.CSS_SELECTOR, 'div.ant-spin-nested-loading > div > span > div > a').text.split('.')[-1].strip()
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'div.ant-spin-nested-loading > div > span > div > a').text.split(attachments_data.file_type)[0].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments4: {}".format(type(e).__name__)) 
                pass
            
            try:
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#grdPublicMessagesGridBeforeInteresttd_thDetailCol a'):
                    detail_clk = single_record.get_attribute("onclick")
                    num_for_url = re.findall('\d{6}',detail_clk)[0]
                    details_att_url = "https://community.vortal.biz/PRODPublic/Tendering/PublicMessageDisplay/Index?id="+str(num_for_url)+"&contractNoticeUniqueIdentifier=&prevCtxUrl=%2fPRODPublic%2fTendering%2fOpportunityDetail%2fIndex%3fPerspective%3dDefault&asPopupView=true"
                    fn.load_page(page_details2,details_att_url,80)
                    
                    try:
                        notice_data.notice_text += page_details2.find_element(By.XPATH, '//*[@id="frmMainForm_tblMainTable"]').get_attribute("outerHTML")                     
                    except:
                        pass
                    
                    try:
                        attachments_data = attachments()
                        
                        external = page_details2.find_element(By.CSS_SELECTOR, 'td.AttachmentSeparator > a').get_attribute('onclick')
                        if "javascript:" in external:
                            external_url = re.findall('\d{8}',external)[0]
                            attachments_data.external_url = "https://community.vortal.biz/PRODPublic/Archive/RetrieveFile/Index?DocumentId="+str(external_url)+"&InCommunity=False&InPaymentGateway=False&DocUniqueIdentifier="                                    
                        else:
                            attachments_data.external_url = external
                        attachments_data.file_type = page_details2.find_element(By.CSS_SELECTOR, 'td.AttachmentSeparator > a').text.split('.')[-1].strip()
                        attachments_data.file_name = page_details2.find_element(By.CSS_SELECTOR, 'td.AttachmentSeparator > a').text.split(attachments_data.file_type)[0].strip()
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
                    except Exception as e:
                        logging.info("Exception in attachments5: {}".format(type(e).__name__)) 
                        pass

            except:
                pass
            
            
            
        else:
            attachments_data = attachments()

            attachments_data.file_name = page_details.find_element(By.XPATH, '''//*[contains(text(),'Peças do procedimento')]//following::td[1]/a''').text
            attachments_data.external_url = lotts_attachments_url
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in lotts_attachments_url2: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) +str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments)
page_details2 = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.base.gov.pt/Base4/pt/pesquisa/?type=anuncios&texto=&numeroanuncio=&emissora=&desdedatapublicacao=&atedatapublicacao=&desdeprecobase=&ateprecobase=&tipoacto=0&tipomodelo=0&tipocontrato=0&cpv="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="advanced_anuncios"]'))).click()
        time.sleep(2)
        date_data = th.strftime('%Y-%m-%d')
        yest_date = page_main.find_element(By.XPATH,'//*[@id="desdedatapublicacao2"]').clear()
        yest_date = page_main.find_element(By.XPATH,'//*[@id="desdedatapublicacao2"]').send_keys(date_data)
        time.sleep(5)
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search_anuncios2"]'))).click()
        time.sleep(2)
        try:
            for page_no in range(1,100):#100
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#page_'+str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr'),page_check))
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
    page_details1.quit()
    page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
