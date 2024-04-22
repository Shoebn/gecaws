import wget
import tarfile
import logging
from gec_common import log_config
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  
import gec_common.web_application_properties as application_properties
from gec_common.gecclass import *
import jsons,re
import gec_common.OutputJSON
import os

download_path = application_properties.TMP_DIR + "/ted_down_file/" 
extract_path = application_properties.TMP_DIR + "/Ted_extract_file/" 

page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
th = date.today() #- timedelta(1)
threshold = th.strftime('%Y/%m/%d')
calendardate = th.strftime('%d/%m/%Y')
logging.info("Scraping from or greater than: " + threshold)

url = 'https://ted.europa.eu/en/simap/xml-bulk-download'
logging.info('----------------------------------')
fn.load_page(page_main, url,80)
logging.info(url)
calendar = page_main.find_element(By.XPATH, '/html/body/div[2]/div/div/div/div[4]/div/section/div/div/div[3]/div/div/section/div/div/div/div/div[2]/table/tbody').text

notice_type_spn = ['10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','CEI']
notice_type_ca = ['25','26','27','28','29','30','31','32','33','34','35','36','37','T02']
notice_type_pp = ['1','2','3','4','5','6','7','8','9','T01']
notice_type_amd = ['38','39','40']

try:
    # rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div/div[4]/div/section/div/div/div[3]/div/div/section/div/div/div/div/div[2]/table/tbody/tr')))
    # length = len(rows)
    # for records in range(0,length):
    #     tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div/div[4]/div/section/div/div/div[3]/div/div/section/div/div/div/div/div[2]/table/tbody/tr')))[records]

    #     line = tender_html_element.text
    #     if "Not yet available" in line:
    #         break
    #     if calendardate in line:        
    #         sline = line.split(' ')
    #         code = sline[1].split('/')[0]
    #         file_year = sline[4].split('/')[2]
    #         file_month = sline[4].split('/')[1]
    #         file_day = sline[4].split('/')[0]
    #         ftp_link = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)>a').get_attribute('href')
    # # home_link = r'ftp://guest:guest@ted.europa.eu/daily-packages/'
    # # ftp_link = home_link + file_year + '/' + file_month + '/' + file_year + file_month + file_day + '_' + file_year + code + '.tar.gz'

    # filef = file_year + file_month + file_day +'_'+ file_year  + code + '.tar.gz'
    # if not os.path.exists(download_path):
    #     os.makedirs(download_path)
    # elif not os.path.exists(extract_path):
    #     os.makedirs(extract_path)
    # else:
    #     pass
    # dd = wget.download(ftp_link, out=download_path)
    # logging.info(dd)

    # fname2 = download_path+filef
    
    # if fname2.endswith("tar.gz"):
    #     tar = tarfile.open(fname2, "r:gz")
    #     code2 = (tar.getnames()[0].split('/')[0])
    #     tar.extractall(extract_path)
    #     tar.close()
    # elif fname2.endswith("tar"):
    #     tar = tarfile.open(fname2, "r:")
    #     code2 = (tar.getnames()[0].split('/')[0])
    #     tar.extractall(extract_path)
    #     tar.close()
    # else:
    #     print('No data')
    NOTICE_DUPLICATE_COUNT = 0
    MAX_NOTICES_DUPLICATE = 4
    MAX_NOTICES = 2000
    notice_count = 0
    SCRIPT_NAME = "eu_tedeuropa"
    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
    previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
    output_json_folder = "jsonfile"
    # XML_PATH = extract_path+ code2 +'/'
    XML_PATH = "/GeC/gecftp/tmp/Ted_extract_file/20240415_074/" #folder_path
    xml_file_name = os.listdir(XML_PATH)
    
    notice_count = 0
    tnotice_count = 0
    list_of_notice_type = {'Additional information':16,'Corrigendum':16,'Corrigenda':16, 'Modification of a contract/concession during its term':16,'Buyer profile' : 0, 'Call for expressions of interest':5, 'Concession award notice':7, 'Contract award notice':7, 'Contract notice':4, 'Design contest':5, 'Dynamic purchasing system':4, 'European company':0, 'European economic interest grouping (eeig)':4, 'General information':4,  'Not applicable':4, 'Other':0, 'Periodic indicative notice with call for competition':3, 'Periodic indicative notice without call for competition':3, 'Prequalification notices':5, 'Prior information notice with call for competition':3, 'Prior information notice without call for competition':3, 'Qualification system with call for competition':5, 'Qualification system without call for competition':5, 'Request for proposals':4, 'Results of design contests':7, 'Services concession':4,'Subcontract notice' : 4, 'Voluntary ex ante transparency notice' : 7, 'Works concession' : 4, 'Works contracts awarded by the concessionnaire' : 4 }
    for xml_file in xml_file_name:
        xml_file = XML_PATH+xml_file
        logging.info(xml_file)    
        with open(xml_file, 'r', encoding='UTF-8') as f:
            soup = BeautifulSoup(f, "xml")
            try:
                notice_data = tender()
                notice_data.procurement_method = 2


                SubTypeCode = soup.find('SubTypeCode').text            
                if str(SubTypeCode) in notice_type_amd:
                    notice_data.notice_type = 16
                    notice_data.script_name = 'eu_tedeuropa_amd'
                elif str(SubTypeCode) in notice_type_ca:
                    notice_data.notice_type = 7
                    notice_data.script_name = 'eu_tedeuropa_ca'
                elif str(SubTypeCode) in notice_type_pp:
                    notice_data.notice_type = 3
                    notice_data.script_name = 'eu_tedeuropa_pp'
                else:
                    notice_data.notice_type = 4
                    notice_data.script_name = 'eu_tedeuropa_spn'

                try:
                    notice_data.notice_no = soup.find_all('efac:Publication')[0].find("efbc:NoticePublicationID").text
                except:
                    pass

                try:
                    published_date = soup.find_all('efac:Publication')[0].find("efbc:PublicationDate").text
                    try:
                        published_date = re.findall('\d{4}\d+\d+',published_date)[0]
                        notice_data.publish_date = datetime.strptime(published_date, '%Y%m%d').strftime('%Y/%m/%d %H:%M:%S')
                        logging.info(notice_data.publish_date)
                    except:
                        published_date = re.findall('\d{4}-\d+-\d+',published_date)[0]
                        notice_data.publish_date = datetime.strptime(published_date, '%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
                        logging.info(notice_data.publish_date)
                except:
                    pass

                try:
                    notice_data.related_tender_id = soup.find_all('efac:Publication')[0].find("efbc:GazetteID").text
                except:
                    pass

                try:
                    notice_data.local_title = soup.find_all("cac:ProcurementProject")[0].find("cbc:Name").text
                except:
                    pass

                try:
                    notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
                except:
                    notice_data.notice_title = notice_data.local_title

                try:
                    notice_data.local_description  = soup.find_all("cac:ProcurementProject")[0].find("cbc:Description").text
                    notice_data.notice_summary_english  = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                except:
                    pass

                try:
                    notice_data.contract_type_actual = soup.find_all("cac:ProcurementProject")[0].find("cbc:ProcurementTypeCode").text
                    if 'services' in notice_data.contract_type_actual.lower():
                        notice_data.notice_contract_type = 'Service'
                    elif 'supplies' in notice_data.contract_type_actual.lower():
                        notice_data.notice_contract_type = 'Supply'
                    elif 'works' in notice_data.contract_type_actual.lower():
                        notice_data.notice_contract_type = 'Works'
                    notice_data.category = notice_data.contract_type_actual
                except:
                    pass

                try:
                    main_language = soup.find('cbc:NoticeLanguageCode').text
                    notice_data.main_language = fn.procedure_mapping("assets/eu_tedeuropa_languagecode.csv",main_language)
                except:
                    pass

                try:
                    customer_details_data = customer_details()
                    org_country = soup.find_all('cac:Country')[0].find("cbc:IdentificationCode").text
                    customer_details_data.org_country = fn.procedure_mapping("assets/ted_countries_iso3.csv",org_country)
                    customer_details_data.org_language = notice_data.main_language
                    try:
                        performance_country_data = performance_country()
                        performance_country_data.performance_country = customer_details_data.org_country
                        performance_country_data.performance_country_cleanup()
                        notice_data.performance_country.append(performance_country_data)
                    except:
                        pass

                    customer_details_data.org_name = soup.find_all('cac:PartyName')[0].find("cbc:Name").text

                    try:
                        customer_details_data.contact_person = soup.find_all("cac:Contact")[0].find("cbc:Name").text
                    except:
                        pass

                    try:
                        customer_details_data.org_email = soup.find_all("cac:Contact")[0].find("cbc:ElectronicMail").text
                    except:
                        pass

                    try:
                        customer_details_data.org_address = soup.find_all("cac:PostalAddress")[0].find("cbc:StreetName").text
                    except:
                        pass

                    try:
                        customer_details_data.org_phone = soup.find_all("cac:Contact")[0].find("cbc:Telephone").text
                    except:
                        pass

                    try:
                        customer_details_data.org_fax = soup.find_all("cac:Contact")[0].find("cbc:Telefax").text
                    except:
                        pass

                    try:
                        customer_details_data.customer_nuts = soup.find_all("cac:PostalAddress")[0].find("cbc:CountrySubentityCode").text
                    except:
                        pass

                    try:
                        customer_details_data.postal_code  = soup.find_all("cac:PostalAddress")[0].find("cbc:PostalZone").text
                    except:
                        pass

                    try:
                        customer_details_data.org_city = soup.find_all("cac:PostalAddress")[0].find("cbc:CityName").text
                    except:
                        pass

                    try:
                        customer_details_data.org_website = soup.find("cbc:WebsiteURI").text
                    except:
                        pass
                    customer_details_data.customer_details_cleanup()
                    notice_data.customer_details.append(customer_details_data)
                except:
                    pass

                try:
                    notice_data.type_of_procedure_actual = soup.find("cbc:ProcedureCode").text
                except:
                    pass

                try:
                    notice_data.type_of_procedure = fn.procedure_mapping("assets/eu_tedeuropa_procedure.csv",notice_data.type_of_procedure_actual)
                except:
                    pass

                try:
                    notice_data.contract_duration = soup.find_all('cac:PlannedPeriod')[0].find("cbc:DurationMeasure").text
                except:
                    pass

                try:
                    EndDate = soup.find_all("cac:TenderSubmissionDeadlinePeriod")[0].find("cbc:EndDate").text
                    EndDate = re.findall('\d{4}-\d+-\d+',EndDate)[0]
                    EndTime = soup.find_all("cac:TenderSubmissionDeadlinePeriod")[0].find("cbc:EndTime").text
                    EndTime = re.findall('\d{2}:\d{2}:\d{2}',EndTime)[0]
                    notice_deadline = EndDate+' '+EndTime
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                    logging.info(notice_data.notice_deadline)
                except:
                    pass

                try:
                    for cpv in soup.find_all("cac:ProcurementProject")[0].find_all("cac:MainCommodityClassification"):
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = cpv.find('cbc:ItemClassificationCode').text
                        notice_data.cpvs.append(cpvs_data)
                except:
                    pass

                try:
                    cpv_at_source = ''
                    for cpv in soup.find_all("cac:ProcurementProject")[0].find_all("cac:MainCommodityClassification"):
                        cpv_at_source += cpv.find('cbc:ItemClassificationCode').text
                        cpv_at_source += ',' 
                    notice_data.cpv_at_source = cpv_at_source.rstrip(',')
                except:
                    pass

                try:
                    month = soup.find("cbc:DurationMeasure").get('unitCode')
                    contract_duration = soup.find("cbc:DurationMeasure").text
                    notice_data.contract_duration = contract_duration+' '+month
                except:
                    pass

                try:
                    lot_info = soup.find_all("cac:ProcurementProjectLot")
                    lot_number = 1
                    for lot in lot_info:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_actual_number = lot.find("cbc:ID").text
                        lot_details_data.lot_title = lot.find_all('cac:ProcurementProject')[0].find("cbc:Name").text
                        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                        try:
                            lot_details_data.lot_description = lot.find_all('cac:ProcurementProject')[0].find('cbc:Description').text
                            lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                        except:
                            pass
                        lot_details_data.contract_type = notice_data.notice_contract_type
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        try:
                            month = lot.find("cbc:DurationMeasure").get('unitCode')
                            contract_duration = lot.find("cbc:DurationMeasure").text
                            lot_details_data.contract_duration = contract_duration+' '+month
                        except:
                            pass
                        try:
                            lot_award_date = soup.find('cbc:AwardDate').text
                            lot_details_data.lot_award_date = datetime.strptime(lot_award_date, '%Y-%m-%d+%H:%M').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass
                        lot_details_data.lot_nuts = customer_details_data.customer_nuts

                        try:
                            for lotcriteria in lot.find_all('cac:SubordinateAwardingCriterion'):
                                lot_criteria_data = lot_criteria()
                                lot_criteria_data.lot_criteria_title = lotcriteria.find("cbc:AwardingCriterionTypeCode").text
                                lot_criteria_data.lot_criteria_weight = int(lotcriteria.find("efbc:ParameterNumeric").text.split('.')[0].strip())
                                lot_criteria_data.lot_criteria_cleanup()
                                lot_details_data.lot_criteria.append(lot_criteria_data)
                        except:
                            pass
                        try:
                            for lotcpv in lot.find_all("cac:MainCommodityClassification"):
                                lot_cpvs_data = lot_cpvs()
                                lot_cpvs_data.lot_cpv_code = lotcpv.find('cbc:ItemClassificationCode').text
                                lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        except:
                            pass

                        try:
                            lot_cpv_at_source = ''
                            for lotcpv in lot.find_all("cac:MainCommodityClassification"):
                                lot_cpv_at_source += lotcpv.find('cbc:ItemClassificationCode').text
                                lot_cpv_at_source += ','
                            lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                        except:
                            pass

                        try:
                            for awarddetails in soup.find_all('efac:LotTender'):
                                try:
                                    TenderLot = awarddetails.find_all("efac:TenderLot")[0].find('cbc:ID').text
                                    if TenderLot in lot_details_data.lot_actual_number:
                                        bidder_name = awarddetails.find_all("efac:TenderingParty")[0].find('cbc:ID').text
                                        try:
                                            for TenderingParty in soup.find_all('efac:TenderingParty'):
                                                tpa_id = TenderingParty.find('cbc:ID').text
                                                if bidder_name in tpa_id:
                                                    for Tenderer in TenderingParty.find_all("efac:Tenderer"):
                                                        Tendererr = Tenderer.find('cbc:ID').text
                                                        for Company in soup.find_all('efac:Company'):
                                                            PartyIdentification = Company.find('cac:PartyIdentification').text
                                                            if Tendererr in PartyIdentification:
                                                                award_details_data = award_details()
                                                                award_details_data.bidder_name = Company.find('cac:PartyName').text.strip()
                                                                award_details_data.award_details_cleanup()
                                                                lot_details_data.award_details.append(award_details_data)
                                        except:
                                            pass
                                except:
                                    pass
                        except:
                            pass

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                except:
                    pass

                try:
                    notice_data.notice_url = 'https://ted.europa.eu/en/notice/-/detail/'+notice_data.notice_no
                    logging.info(notice_data.notice_url)
                except:
                    pass

                try:        
                    fn.load_page(page_details,notice_data.notice_url,120)
                    try:
                        notice_data.notice_text = WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div/div/div[3]'))).get_attribute('outerHTML')
                    except:
                        notice_data.notice_text = WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content"]'))).get_attribute('outerHTML')
                except:
                    pass

                notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
                notice_data.tender_cleanup()
                output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
                notice_count += 1
                tnotice_count += 1
            except:
                notice_data = tender()
                notice_data.procurement_method = 2
                notice_data.script_name = 'eu_tedeuropa_spn'
                notice_data.notice_type = 4
                try:
                    notice_data.notice_no = soup.find("RECEPTION_ID").text
                except:
                    pass

                try:
                    notice_data.related_tender_id = soup.find("NO_DOC_OJS").text
                except:
                    pass

                try:
                    notice_data.additional_tender_url = soup.find("IA_URL_GENERAL").text
                except:
                    pass

                try:
                    notice_data.type_of_procedure_actual = soup.find("PR_PROC").text
                except:
                    pass

                try:
                    published_date = soup.find("DATE_PUB").text
                    notice_data.publish_date = datetime.strptime(published_date, '%Y%m%d').strftime('%Y/%m/%d')
                    logging.info(notice_data.publish_date)
                except:
                    pass

                try:
                    document_opening_time = soup.find("DATE_OPENING_TENDERS").text
                    notice_data.document_opening_time = datetime.strptime(document_opening_time, '%Y-%m-%d').strftime('%Y-%m-%d')
                except:
                    pass

                try:
                    notice_type = soup.find("TD_DOCUMENT_TYPE").text
                    if notice_type in list_of_notice_type:
                        notice_data.notice_type = list_of_notice_type[notice_type]
                        if notice_data.notice_type == 16:
                            notice_data.script_name = 'eu_tedeuropa_amd'
                        elif notice_data.notice_type == 7:
                            notice_data.script_name = 'eu_tedeuropa_ca'
                        elif notice_data.notice_type == 3:
                            notice_data.script_name = 'eu_tedeuropa_pp'
                        else:
                            notice_data.script_name = 'eu_tedeuropa_spn'
                    notice_data.document_type_description = soup.find("TD_DOCUMENT_TYPE").text
                except:
                    pass

                try:
                    notice_data.category = soup.find("NC_CONTRACT_NATURE").text
                    if 'Services' in notice_data.category:
                        notice_data.notice_contract_type = 'Service'
                    elif 'Supplies' in notice_data.category:
                        notice_data.notice_contract_type = 'Supply'
                    elif 'Works' in notice_data.category:
                        notice_data.notice_contract_type = 'Works'
                except:
                    pass

                try:
                    notice_data.local_title = soup.find_all("OBJECT_CONTRACT")[0].find("TITLE").text
                    notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
                except:
                    try:
                        notice_data.local_title = soup.find("TITLE_CONTRACT").text
                        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
                    except:
                        pass

                try:
                    notice_data.local_description  = soup.find_all("OBJECT_CONTRACT")[0].find("SHORT_DESCR").text
                    notice_data.notice_summary_english  = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                except:
                    try:
                        notice_data.local_description  = soup.find("SHORT_CONTRACT_DESCRIPTION").text
                        notice_data.notice_summary_english  = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                    except:
                        pass

                try:
                    notice_deadline = soup.find("DT_DATE_FOR_SUBMISSION").text.split(' ')[0]
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y%m%d').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    pass

                try:
                    dispatch_date = soup.find("DS_DATE_DISPATCH").text.split(' ')[0]
                    notice_data.dispatch_date = datetime.strptime(dispatch_date,'%Y%m%d').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    pass

                try:
                    for cpv in soup.find_all("ORIGINAL_CPV"):
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = cpv.get('CODE')
                        notice_data.cpvs.append(cpvs_data)
                except:
                    pass

                try:
                    for AC_QUALITY in soup.find_all("AC_QUALITY")[:1]:
                        tender_criteria_data = tender_criteria()
                        tender_criteria_data.tender_criteria_title = AC_QUALITY.find("AC_CRITERION").text
                        try:
                            tender_criteria_data.tender_criteria_weight = int(AC_QUALITY.find("AC_WEIGHTING").text.replace('%','').strip())
                        except:
                            pass
                        tender_criteria_data.tender_is_price_related = False
                        tender_criteria_data.tender_criteria_cleanup()
                        notice_data.tender_criteria.append(tender_criteria_data)
                        try:
                            tender_criteria_data = tender_criteria()
                            tender_is_price_related  = soup.find_all("AC_PRICE")[0].find("AC_WEIGHTING").text
                            tender_criteria_data.tender_criteria_title = 'Price'
                            tender_criteria_data.tender_criteria_weight = int(tender_is_price_related.replace('%','').strip())
                            tender_criteria_data.tender_is_price_related = True
                            tender_criteria_data.tender_criteria_cleanup()
                            notice_data.tender_criteria.append(tender_criteria_data)
                        except:
                            pass
                except:
                    pass

                try:
                    notice_data.main_language = soup.find("LG_ORIG").text
                except:
                    pass

                try:
                    performance_country_data = performance_country()
                    performance_country_data.performance_country = soup.find_all("ISO_COUNTRY")[0].get('VALUE')
                    if 'UK' in performance_country_data.performance_country:
                        performance_country_data.performance_country = 'GB'
                    performance_country_data.performance_country_cleanup()
                    notice_data.performance_country.append(performance_country_data)
                except:
                    pass
                customer_details_data = customer_details()
                customer_details_data.org_country = performance_country_data.performance_country
                try:
                    org_name = soup.find("OFFICIALNAME").text
                    if notice_data.main_language == 'FR':
                        customer_details_data.org_name = GoogleTranslator(source='fr', target='en').translate(org_name)
                    else:
                        customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)  
                    customer_details_data.org_language = notice_data.main_language
                except:
                    pass

                try:
                    contact_person = soup.find_all("ADDRESS_CONTRACTING_BODY")[0].find("CONTACT_POINT").text
                    customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
                except:
                    pass

                try:
                    org_address = soup.find_all("ADDRESS_CONTRACTING_BODY")[0].find("ADDRESS").text
                    customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
                    try:
                        address2 = soup.find_all("ADDRESS_FURTHER_INFO")[0].find("ADDRESS").text
                        customer_details_data.org_address += GoogleTranslator(source='auto', target='en').translate(address2)
                    except:
                        pass
                except:
                    pass

                try:
                    customer_details_data.org_phone = soup.find_all("ADDRESS_CONTRACTING_BODY")[0].find("PHONE").text
                except:
                    pass

                try:
                    customer_details_data.customer_nuts = soup.find("n2021:PERFORMANCE_NUTS").text
                except:
                    pass

                try:
                    customer_details_data.customer_main_activity  = soup.find("MA_MAIN_ACTIVITIES").text
                except:
                    pass

                try:
                    customer_details_data.postal_code  = soup.find("POSTAL_CODE").text
                except:
                    pass

                try:
                    customer_details_data.org_email = soup.find_all("ADDRESS_CONTRACTING_BODY")[0].find("E_MAIL").text
                except:
                    pass

                try:
                    org_city = soup.find_all("ADDRESS_CONTRACTING_BODY")[0].find("TOWN").text
                    customer_details_data.org_city = GoogleTranslator(source='auto', target='en').translate(org_city)
                except:
                    pass
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)

                try:
                    month = soup.find_all("DURATION")[0].get('TYPE')
                    contract_duration = soup.find_all("DURATION")[0].text
                    notice_data.contract_duration = contract_duration+' '+month
                except:
                    pass

                try:
                    LOT_DIVISION = soup.find('LOT_DIVISION')
                    if ('LOT_DIVISION') in str(LOT_DIVISION):
                        lot_info = soup.find_all("OBJECT_DESCR")
                        lot_number = 1
                        for lot in lot_info:
                            lot_details_data = lot_details()
                            lot_details_data.lot_number = lot_number
                            lot_details_data.lot_actual_number = lot.find("LOT_NO").text
                            lot_title = lot.find("TITLE").text
                            lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                            try:
                                lot_description = lot.find('SHORT_DESCR').text
                                lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
                            except:
                                pass
                            lot_details_data.contract_type = notice_data.notice_contract_type
                            lot_details_data.contract_duration = notice_data.contract_duration
                            lot_details_data.lot_nuts = customer_details_data.customer_nuts
                            try:
                                contract_start_date = soup.find("DATE_START").text.split(' ')[0]
                                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
                            except:
                                pass

                            try:
                                contract_end_date = soup.find("DATE_END").text.split(' ')[0]
                                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
                            except:
                                pass
                            try:
                                for AC_QUALITY in lot.find_all("AC_QUALITY"):
                                    lot_criteria_data = lot_criteria()
                                    lot_criteria_data.lot_criteria_title = AC_QUALITY.find("AC_CRITERION").text
                                    try:
                                        lot_criteria_data.lot_criteria_weight = int(AC_QUALITY.find("AC_WEIGHTING").text.replace('%','').strip())
                                    except:
                                        pass
                                    lot_criteria_data.lot_is_price_related = False
                                    lot_criteria_data.lot_criteria_cleanup()
                                    lot_details_data.lot_criteria.append(lot_criteria_data)
                                    try:
                                        lot_criteria_data = lot_criteria()
                                        lot_is_price_related  = lot.find_all("AC_PRICE")[0].find("AC_WEIGHTING").text
                                        lot_criteria_data.lot_criteria_title = 'Price'
                                        lot_criteria_data.lot_criteria_weight = int(lot_is_price_related.replace('%','').strip())
                                        lot_criteria_data.lot_is_price_related = True
                                        lot_criteria_data.lot_criteria_cleanup()
                                        lot_details_data.lot_criteria.append(lot_criteria_data)
                                    except:
                                        pass
                            except:
                                pass
                            try:
                                CPV_ADDITIONAL = lot.find_all('CPV_ADDITIONAL')
                                for cpv in CPV_ADDITIONAL:
                                    lot_cpvs_data = lot_cpvs()
                                    lot_cpvs_data.lot_cpv_code = cpv.find("CPV_CODE").get('CODE')
                                    lot_cpvs_data.lot_cpvs_cleanup()
                                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                            except:
                                pass

                            try:
                                if notice_data.notice_type == 7:
                                    award_details_data = award_details()
                                    bidder_name = soup.find_all("ADDRESS_CONTRACTOR")[0].find("OFFICIALNAME").text
                                    award_details_data.bidder_name = GoogleTranslator(source='auto', target='en').translate(bidder_name)
                                    try:
                                        award_details_data.grossawardvaluelc = float(soup.find_all("AWARDED_CONTRACT")[0].find("grossawardvaluelc").text)
                                    except:
                                        pass

                                    try:
                                        awarding_company_address = soup.find_all("ADDRESS_CONTRACTOR")[0].find("ADDRESS").text
                                        award_details_data.address = GoogleTranslator(source='auto', target='en').translate(awarding_company_address)
                                    except:
                                        pass

                                    try:
                                        award_details_data.bid_recieved = soup.find_all("AWARDED_CONTRACT")[0].find("NB_TENDERS_RECEIVED").text
                                    except:
                                        pass
                                    award_details_data.award_details_cleanup()
                                    lot_details_data.award_details.append(award_details_data)
                            except:
                                pass
                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number += 1
                    else:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = 1
                        lot_details_data.lot_title = notice_data.notice_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_description = notice_data.notice_summary_english
                        lot_details_data.contract_duration = notice_data.contract_duration
                        lot_details_data.contract_type = notice_data.notice_contract_type
                        lot_details_data.lot_nuts = customer_details_data.customer_nuts
                        for lot_cpv in notice_data.cpvs:
                            lot_cpvs_data = lot_cpvs()
                            lot_cpvs_data.lot_cpv_code = lot_cpv.cpv_code
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        try:
                            contract_start_date = soup.find("DATE_START").text.split(' ')[0]
                            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass

                        try:
                            contract_end_date = soup.find("DATE_END").text.split(' ')[0]
                            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass
                        try:
                            if notice_data.notice_type == 7:
                                award_details_data = award_details()
                                bidder_name = soup.find_all("ADDRESS_CONTRACTOR")[0].find("OFFICIALNAME").text
                                award_details_data.bidder_name = GoogleTranslator(source='auto', target='en').translate(bidder_name)
                                try:
                                    award_details_data.grossawardvaluelc = float(soup.find_all("AWARDED_CONTRACT")[0].find("VAL_TOTAL").text)
                                except:
                                    pass

                                try:
                                    awarding_company_address = soup.find_all("ADDRESS_CONTRACTOR")[0].find("ADDRESS").text
                                    award_details_data.address = GoogleTranslator(source='auto', target='en').translate(awarding_company_address)
                                except:
                                    pass

                                try:
                                    award_details_data.bid_recieved = soup.find_all("AWARDED_CONTRACT")[0].find("NB_TENDERS_RECEIVED").text
                                except:
                                    pass
                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)
                        except:
                            pass
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                except:
                    pass
                try:
                    notice_data.project_name = soup.find("EU_PROGR_RELATED").text 
                except:
                    pass

                try:
                    notice_url = soup.find("URI_DOC").text 
                    notice_data.notice_url = notice_url
                    logging.info(notice_data.notice_url)
                except:
                    pass

                try:        
                    fn.load_page(page_details,notice_data.notice_url,120)
                    try:
                        notice_data.notice_text = WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div/div/div[3]'))).get_attribute('outerHTML')
                    except:
                        notice_data.notice_text = WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content"]'))).get_attribute('outerHTML')
                except:
                    pass

                try:
                    est_amount = soup.find("VALUE").text
                    notice_data.est_amount = float(re.sub("[^\d\.]", "", est_amount))
                    notice_data.grossbudgetlc = notice_data.est_amount
                except:
                    pass

                try:
                    notice_data.currency = soup.find_all("VALUE")[0].get('CURRENCY')
                except:
                    pass

                try:
                    EU_PROGR_RELATED = soup.find('EU_PROGR_RELATED')
                    if ('EU_PROGR_RELATED') in str(EU_PROGR_RELATED):
                        if notice_data.funding_agencies == []:
                            funding_agencies_data = funding_agencies()
                            funding_agencies_data.funding_agency = 7314301
                            funding_agencies_data.funding_agencies_cleanup()
                            notice_data.funding_agencies.append(funding_agencies_data)
                except:
                    pass

                try:
                    NO_EU_PROGR_RELATED = soup.find('NO_EU_PROGR_RELATED')
                    if ('NO_EU_PROGR_RELATED') in str(NO_EU_PROGR_RELATED):
                        notice_data.funding_agencies = []
                except:
                    pass
                notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
                notice_data.tender_cleanup()
                output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
                notice_count += 1
                tnotice_count += 1
        os.remove(xml_file)
        logging.info('----------------------------------')
        if notice_count == 50:
            output_json_file.copyFinalJSONToServer(output_json_folder)
            output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
            notice_count = 0
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e)) 
finally:
    page_main.quit()    
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
