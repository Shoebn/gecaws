from datetime import date, datetime, timedelta

import gec_common.cpv_list as main_cpv_list

import gec_common.functions as fn

list_source_of_funds = ['Others','Self Funded','Government funded','International agencies','NGO',"Own"]

list_class_at_source = ['OTHERS','UNSPSC','NAICS','CPV','HSCode','BPM6','GSIN']

list_notice_contract_type = ['Service','Works','Supply','Consultancy','Non consultancy']

list_notice_types = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

list_procurement_method = [0,1,2]

list_bidding_response_method = ['Electronic','Manual','Not Available']

list_of_procedure = ['Competitive dialogue','Competitive tendering','Concession award procedure','Concession award without prior concession notice','Contract award without prior publication','Direct award','Innovation partnership','Negotiated procedure','Negotiated with prior publication of a call for competition /   competitive with negotiation','Negotiated without prior call for competition','Open','Other','Other multiple stage procedure','Other single stage procedure','Restricted']
        
class lot_cpvs:
    def __init__(self):
        self.lot_cpv_code = None

    def lot_cpvs_cleanup(self):
        if self.lot_cpv_code == '':
            self.lot_cpv_code = None
        

class cpvs:
    def __init__(self):
        self.cpv_code = None
    def cpvs_cleanup(self):
        if self.cpv_code == '':
            self.cpv_code = None
        
class funding_agencies:
    def __init__(self):
        self.funding_agency: int = None
    def funding_agencies_cleanup(self):
        if type(self.funding_agency) is str:
            self.funding_agency = int(self.funding_agency)
        if self.funding_agency == '':
            self.funding_agency = None
        
class performance_country:
    def __init__(self):
        self.performance_country: str = None #character varying(4000) ,
    def performance_country_cleanup(self):
        if self.performance_country == '':
            self.performance_country = None
        if self.performance_country is not None:
            self.performance_country = self.performance_country[:2].strip()       
        
class performance_state:
    def __init__(self):
        self.performance_state: str = None #character varying(60),
    def performance_state_cleanup(self):
        if self.performance_state == '':
            self.performance_state = None        

class attachments:
    def __init__(self):
        self.file_type: str = None #character varying(60)
        self.file_name: str = None #character varying(500)
        self.file_description: str = None #character(500)
        self.external_url: str = None #character varying(4000)
        self.file_size: float = 0.00 #character varying(80)
       
    def attachments_cleanup(self):
        if self.file_type == '':
            self.file_type = None  
            
        if self.file_type is not None:
            self.file_type = self.file_type[:60].strip()
            
        if self.file_name == '':
            self.file_name = None  
            
        if self.file_name is not None:
            self.file_name = self.file_name[:500].strip()
        
        if self.file_description == '':
            self.file_description = None
            
        if self.file_description is not None:
            self.file_description = self.file_description[:500].strip()
        
        if self.external_url == '':
            self.external_url = None
            
        if self.external_url is not None:
            self.external_url = self.external_url[:4000].strip()
            
        if self.file_description is None and self.file_name is not None:
            self.file_description = self.file_name
        
        if self.file_size is not None:
            try:
                if type(self.file_size) is float:
                    self.file_size = self.file_size
                elif 'kb' in self.file_size.lower() or 'kilobytes' in self.file_size.lower():
                    filesize = self.file_size.lower().replace('kb','').replace('kilobytes','').replace(',','.').strip()
                    self.file_size = float(filesize) * 1024
                elif 'mb' in self.file_size.lower() or 'megabytes' in self.file_size.lower():
                    filesize = self.file_size.lower().replace('mb','').replace('megabytes','').replace(',','.').strip()
                    self.file_size = float(filesize) * 1024 * 1024
                elif 'gb' in self.file_size.lower() or 'gigabytes' in self.file_size.lower():
                    filesize = self.file_size.lower().replace('gb','').replace('gigabytes','').replace(',','.').strip()
                    self.file_size = float(filesize) * 1024 * 1024 * 1024
                elif float(self.file_size) > 1024:
                    self.file_size = float(self.file_size)
                else:
                    self.file_size = 0.00
            except:
                self.file_size = 0.00
                
        if self.file_size != 0.00:
            file_size = str(self.file_size).split('.')
            if len(file_size[0]) > 20:
                self.file_size = 0.00
            
        
class award_details:
    def __init__(self):
        self.bidder_country:str = None
        self.bidder_name: str = None #text
        self.address: str = None #character varying(255)
        self.initial_estimated_value: float = 0.00 #character varying(40)
        self.final_estimated_value: float = 0.00 #character varying(40)
        self.bid_recieved: str = None # character varying(10)
        self.contract_duration: str = None # character varying(500)
        self.award_date: date = None # timestamp without time zone
        self.winner_group_name: str = None # text
        self.grossawardvalueeuro: float = 0.00 # numeric(20,2),
        self.netawardvalueeuro: float = 0.00 #numeric(20,2),
        self.grossawardvaluelc: float = 0.00 #numeric(20,2),
        self.netawardvaluelc: float = 0.00 #numeric(12,2),
        self.award_quantity: float = 0.00 #numeric(12,2),
        self.notes: str = None #text
       
    def award_details_cleanup(self):
        if self.bidder_country == '':
            self.bidder_country = None
        
        if self.bidder_name == '':
            self.bidder_name = None
        
        if self.address == '':
            self.address = None
        
        if self.bid_recieved == '':
            self.bid_recieved = None
        
        if self.contract_duration == '':
            self.contract_duration = None
        
        if self.award_date == '':
            self.award_date = None
        
        if self.winner_group_name == '':
            self.winner_group_name = None
        
        if self.notes == '':
            self.notes = None
            
        if self.bidder_country is not None:
            self.bidder_country = self.bidder_country[:2].strip()
        if self.bidder_name is not None:
            self.bidder_name = self.bidder_name[:2000].strip()
        if self.winner_group_name is not None:
            self.winner_group_name = self.winner_group_name[:2000].strip() 
        if self.address is not None:
            self.address = self.address[:255].strip()   
        if self.bid_recieved is not None:
            self.bid_recieved = self.bid_recieved[:10].strip()  
        if self.contract_duration is not None:
            self.contract_duration = self.contract_duration[:500].strip()

        if type(self.award_date) is str:
            self.award_date = datetime.strptime(self.award_date, '%Y/%m/%d').date()

        if self.award_date is not None:
            self.award_date = fn.date(str(self.award_date))
            
        if type(self.initial_estimated_value) is float:
            self.initial_estimated_value = float("%.2f" % self.initial_estimated_value)
        elif type(self.initial_estimated_value) is int:
            self.initial_estimated_value = float(self.initial_estimated_value)
        else:
            self.initial_estimated_value = 0.00
            
        if type(self.final_estimated_value) is float:
            self.final_estimated_value = float("%.2f" % self.final_estimated_value)
        elif type(self.final_estimated_value) is int:
            self.final_estimated_value = float(self.final_estimated_value)
        else:
            self.final_estimated_value = 0.00
            
        if type(self.grossawardvalueeuro) is float:
            self.grossawardvalueeuro = float("%.2f" % self.grossawardvalueeuro)
        elif type(self.grossawardvalueeuro) is int:
            self.grossawardvalueeuro = float(self.grossawardvalueeuro)
        else:
            self.grossawardvalueeuro = 0.00

        if type(self.netawardvalueeuro) is float:
            self.netawardvalueeuro = float("%.2f" % self.netawardvalueeuro)
        elif type(self.netawardvalueeuro) is int:
            self.netawardvalueeuro = float(self.netawardvalueeuro)
        else:
            self.netawardvalueeuro = 0.00

        if type(self.grossawardvaluelc) is float:
            self.grossawardvaluelc = float("%.2f" % self.grossawardvaluelc)
        elif type(self.grossawardvaluelc) is int:
            self.grossawardvaluelc = float(self.grossawardvaluelc)
        else:
            self.grossawardvaluelc = 0.00

        if type(self.netawardvaluelc) is float:
            self.netawardvaluelc = float("%.2f" % self.netawardvaluelc)
        elif type(self.netawardvaluelc) is int:
            self.netawardvaluelc = float(self.netawardvaluelc)
        else:
            self.netawardvaluelc = 0.00

        if type(self.award_quantity) is float:
            self.award_quantity = float("%.2f" % self.award_quantity)
        elif type(self.award_quantity) is int:
            self.award_quantity = float(self.award_quantity)
        else:
            self.award_quantity = 0.00

        if self.bidder_name == None and (self.address != None or self.initial_estimated_value != 0.00 or self.final_estimated_value != 0.00 or self.bid_recieved != None or self.contract_duration != None or self.award_date != None or self.winner_group_name != None or self.grossawardvalueeuro != 0.00 or self.netawardvalueeuro != 0.00 or self.grossawardvaluelc != 0.00 or self.netawardvaluelc != 0.00 or self.award_quantity != 0.00 or self.notes != None):
            self.bidder_name = 'N/A'

        if self.initial_estimated_value != 0.00:
            initial_estimated_value = str(self.initial_estimated_value).split('.')
            if len(initial_estimated_value[0]) > 20:
                self.initial_estimated_value = 0.00

        if self.final_estimated_value != 0.00:
            final_estimated_value = str(self.final_estimated_value).split('.')
            if len(final_estimated_value[0]) > 20:
                self.final_estimated_value = 0.00

        if self.grossawardvalueeuro != 0.00:
            grossawardvalueeuro = str(self.grossawardvalueeuro).split('.')
            if len(grossawardvalueeuro[0]) > 20:
                self.grossawardvalueeuro = 0.00

        if self.netawardvalueeuro != 0.00:
            netawardvalueeuro = str(self.netawardvalueeuro).split('.')
            if len(netawardvalueeuro[0]) > 20:
                self.netawardvalueeuro = 0.00

        if self.grossawardvaluelc != 0.00:
            grossawardvaluelc = str(self.grossawardvaluelc).split('.')
            if len(grossawardvaluelc[0]) > 20:
                self.grossawardvaluelc = 0.00

        if self.netawardvaluelc != 0.00:
            netawardvaluelc = str(self.netawardvaluelc).split('.')
            if len(netawardvaluelc[0]) > 20:
                self.netawardvaluelc = 0.00

        if self.award_quantity != 0.00:
            award_quantity = str(self.award_quantity).split('.')
            if len(award_quantity[0]) > 20:
                self.award_quantity = 0.00
                
class lot_criteria:
    def __init__(self):        
        self.lot_criteria_title: str = None # text ,
        self.lot_criteria_weight: int = 0 # bit(1),
        self.lot_is_price_related: bool = False # text
       
    def lot_criteria_cleanup(self):
        if self.lot_criteria_title == '':
            self.lot_criteria_title = None
            
        if self.lot_criteria_title is not None:
            self.lot_criteria_title = self.lot_criteria_title[:1000].strip() 
            if ('price' in self.lot_criteria_title or 'Price' in self.lot_criteria_title) and self.lot_criteria_weight > 0:
                self.lot_is_price_related = True
       
class tender_criteria:
    def __init__(self):  
        self.tender_criteria_title: str = None # text ,
        self.tender_criteria_weight: int = 0 # bit(1),
        self.tender_is_price_related: bool = False # text
       
    def tender_criteria_cleanup(self):
        if self.tender_criteria_title == '':
            self.tender_criteria_title = None
            
        if self.tender_criteria_title is not None:
            if ('price' in self.tender_criteria_title or 'Price' in self.tender_criteria_title) and self.tender_criteria_weight > 0:
                self.tender_is_price_related = True
                    
class lot_details:
    def __init__(self):
        self.lot_contract_type_actual: str = None #  character varying(500) ,
        self.lot_actual_number: str = None #  character varying(100) ,
        self.lot_number: int = None #  character varying(4000) ,
        self.lot_title: str  = None # character varying(4000) ,
        self.lot_title_english: str = None # character varying(4000) ,
        self.lot_description: str = None #  character varying(4000) ',
        self.lot_class_codes_at_source : str = None
        self.lot_cpv_at_source: str = None
        self.lot_description_english: str = None
        self.lot_grossbudget: float  = 0.00 # numeric(20,2) DEFAULT 'NULL::numeric',
        self.lot_netbudget: float  = 0.00 # numeric(20,2) DEFAULT 'NULL::numeric',
        self.lot_grossbudget_lc: float  = 0.00 # numeric(20,2) DEFAULT 'NULL::numeric',
        self.lot_netbudget_lc: float  = 0.00 # numeric(20,2) DEFAULT 'NULL::numeric',
        self.lot_vat: float  = 0.00 #  numeric(20,2) DEFAULT 'NULL::numeric',
        self.lot_quantity: float = None
        self.lot_min_quantity: float  = 0.00 #  numeric(15,2) DEFAULT 'NULL::numeric',
        self.lot_max_quantity: float  = 0.00 #  numeric(15,2) DEFAULT 'NULL::numeric',
        self.lot_quantity_uom: str  = None # numeric(15,2) DEFAULT 'NULL::numeric',
        self.contract_number: str  = None # character varying(4000) ',
        self.contract_duration: str  = None # integer,
        self.contract_start_date: datetime = None # timestamp without time zone,
        self.contract_end_date: datetime = None # timestamp without time zone,
        self.lot_nuts: str  = None # character varying(4000) ',
        self.lot_is_canceled: bool = False #  bit(1) DEFAULT 'NULL::"bit"',
        self.lot_cancellation_date: datetime  = None # date,
        self.lot_award_date: datetime  = None # date,
        self.lot_cpvs  = [] # character varying(4000) ',
        self.contract_type:str = None #  character varying(4000)
        self.lot_criteria = [] #class lot_criteria
        self.award_details = [] #class award_details
       
    def lot_details_cleanup(self):
        if self.lot_contract_type_actual == '':
            self.lot_contract_type_actual = None
            
        if self.lot_actual_number == '':
            self.lot_actual_number = None
            
        if self.lot_number == '':
            self.lot_number = None
            
        if self.lot_title == '':
            self.lot_title = None
            
        if self.lot_title_english == '':
            self.lot_title_english = None
            
        if self.lot_description == '':
            self.lot_description = None
            
        if self.lot_class_codes_at_source == '':
            self.lot_class_codes_at_source = None
            
        if self.lot_description_english == '':
            self.lot_description_english = None
            
        if self.lot_quantity_uom == '':
            self.lot_quantity_uom = None
            
        if self.contract_number == '':
            self.contract_number = None
            
        if self.contract_duration == '':
            self.contract_duration = None
            
        if self.contract_start_date == '':
            self.contract_start_date = None
            
        if self.contract_end_date == '':
            self.contract_end_date = None
            
        if self.lot_nuts == '':
            self.lot_nuts = None
            
        if self.lot_cancellation_date == '':
            self.lot_cancellation_date = None
            
        if self.lot_award_date == '':
            self.lot_award_date = None
            
        if self.contract_type == '':
            self.contract_type = None
        
        if self.lot_quantity_uom is not None and self.lot_quantity is None:
            self.lot_quantity_uom = self.lot_quantity_uom[:50].strip()
            self.lot_quantity = 0.00
        elif self.lot_quantity_uom is None and self.lot_quantity is None:
            self.lot_quantity = 1.00
                
        if self.lot_title is not None:
            self.lot_title = self.lot_title[:4000].strip() 

        if self.lot_title_english is not None:
            self.lot_title_english = self.lot_title_english[:4000].strip()

        if self.lot_cpv_at_source == '':
            self.lot_cpv_at_source = None

        if self.lot_class_codes_at_source  is not None:
            self.lot_class_codes_at_source  = self.lot_class_codes_at_source [:500].strip()
                
        if self.lot_title is not None and self.lot_title_english is None:
            self.lot_title_english = self.lot_title 
                
        if self.lot_cpvs != []:
            for cpv in self.lot_cpvs:
                if cpv.lot_cpv_code not in main_cpv_list.cpv_list:
                    self.lot_cpvs = []
                        
        if (self.lot_cpvs == [] and self.lot_title_english is not None) or (self.lot_cpvs == [''] and self.lot_title_english is not None):
            cpv_list = fn.assign_cpvs_from_title(self.lot_title_english.lower())
            for cpv in cpv_list:
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = cpv
                self.lot_cpvs.append(lot_cpvs_data)
        
        #if self.lot_cpvs == []:
        #lot_cpvs_data = lot_cpvs()
        #lot_cpvs_data.lot_cpv_code = cpvs.cpv_code
        #self.lot_cpvs.append(lot_cpvs_data) 
                
        if self.lot_actual_number is not None:
            self.lot_actual_number = self.lot_actual_number[:100].strip()
                
        
        if type(self.lot_grossbudget) is float:
            self.lot_grossbudget = float("%.2f" % self.lot_grossbudget)
        elif type(self.lot_grossbudget) is int:
            self.lot_grossbudget = float(self.lot_grossbudget)
        else:
            self.lot_grossbudget = 0.00

        if type(self.lot_netbudget) is float:
            self.lot_netbudget = float("%.2f" % self.lot_netbudget)
        elif type(self.lot_netbudget) is int:
            self.lot_netbudget = float(self.lot_netbudget)
        else:
            self.lot_netbudget = 0.00

        if type(self.lot_grossbudget_lc) is float:
            self.lot_grossbudget_lc = float("%.2f" % self.lot_grossbudget_lc)
        elif type(self.lot_grossbudget_lc) is int:
            self.lot_grossbudget_lc = float(self.lot_grossbudget_lc)
        else:
            self.lot_grossbudget_lc = 0.00

        if type(self.lot_netbudget_lc) is float:
            self.lot_netbudget_lc = float("%.2f" % self.lot_netbudget_lc)
        elif type(self.lot_netbudget_lc) is int:
            self.lot_netbudget_lc = float(self.lot_netbudget_lc)
        else:
            self.lot_netbudget_lc = 0.00

        if type(self.lot_vat) is float:
            self.lot_vat = float("%.2f" % self.lot_vat)
        elif type(self.lot_vat) is int:
            self.lot_vat = float(self.lot_vat)
        else:
            self.lot_vat = 0.00
        
        if type(self.lot_quantity) is float:
            self.lot_quantity = float("%.2f" % self.lot_quantity)
        elif type(self.lot_quantity) is int:
            self.lot_quantity = float(self.lot_quantity)
        else:
            self.lot_quantity = 1.00
        
        if type(self.lot_min_quantity) is float:
            self.lot_min_quantity = float("%.2f" % self.lot_min_quantity)
        elif type(self.lot_min_quantity) is int:
            self.lot_min_quantity = float(self.lot_min_quantity)
        else:
            self.lot_min_quantity = 0.00

        if type(self.lot_max_quantity) is float:
            self.lot_max_quantity = float("%.2f" % self.lot_max_quantity)
        elif type(self.lot_max_quantity) is int:
            self.lot_max_quantity = float(self.lot_max_quantity)
        else:
            self.lot_max_quantity = 0.00

        if self.contract_number is not None:
            self.contract_number = self.contract_number[:100].strip()  
        
        if self.lot_nuts is not None:
            self.lot_nuts = self.lot_nuts[:200].strip()
            
        if self.contract_duration is not None:
            self.contract_duration = self.contract_duration[:500].strip() 
        
        if self.contract_start_date is not None:
            try:
                self.contract_start_date = datetime.strptime(self.contract_start_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.contract_start_date = fn.date(str(self.contract_start_date))
        
        if self.contract_end_date is not None:
            try:
                self.contract_end_date = datetime.strptime(self.contract_end_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.contract_end_date = fn.date(str(self.contract_end_date))
        
        if self.lot_cancellation_date is not None:
            try:
                self.lot_cancellation_date = datetime.strptime(self.lot_cancellation_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.lot_cancellation_date = fn.date(str(self.lot_cancellation_date))
        
        if self.lot_award_date is not None:
            try:
                self.lot_award_date = datetime.strptime(self.lot_award_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.lot_award_date = fn.date(str(self.lot_award_date))
        
        if self.contract_type is not None:
            self.contract_type = self.contract_type[:100].strip()
            
        if self.lot_contract_type_actual is not None:
            self.lot_contract_type_actual = self.lot_contract_type_actual[:500].strip()
            
        if self.lot_cpvs != []:
            self.lot_cpvs = list({v.lot_cpv_code:v for v in self.lot_cpvs}.values())

        if self.lot_cpv_at_source is not None:
            cpv_at_source_unique = self.lot_cpv_at_source.split(',')
            cpv_at_source_unique_list = list(dict.fromkeys(cpv_at_source_unique))
        
            lot_cpv_at_source = ''
            for cpv in cpv_at_source_unique_list:
                lot_cpv_at_source += cpv 
                lot_cpv_at_source += ',' 
            self.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
            
        if self.lot_criteria != []:
            for lot_criteria in self.lot_criteria:
                if lot_criteria.lot_criteria_title is None:
                    self.lot_criteria = []

        if self.lot_grossbudget != 0.00:
            lot_grossbudget = str(self.lot_grossbudget).split('.')
            if len(lot_grossbudget[0]) > 20:
                self.lot_grossbudget = 0.00

        if self.lot_netbudget != 0.00:
            lot_netbudget = str(self.lot_netbudget).split('.')
            if len(lot_netbudget[0]) > 20:
                self.lot_netbudget = 0.00

        if self.lot_grossbudget_lc != 0.00:
            lot_grossbudget_lc = str(self.lot_grossbudget_lc).split('.')
            if len(lot_grossbudget_lc[0]) > 20:
                self.lot_grossbudget_lc = 0.00

        if self.lot_netbudget_lc != 0.00:
            lot_netbudget_lc = str(self.lot_netbudget_lc).split('.')
            if len(lot_netbudget_lc[0]) > 20:
                self.lot_netbudget_lc = 0.00

        if self.lot_vat != 0.00:
            lot_vat = str(self.lot_vat).split('.')
            if len(lot_vat[0]) > 20:
                self.lot_vat = 0.00

        if self.lot_quantity != 0.00:
            lot_quantity = str(self.lot_quantity).split('.')
            if len(lot_quantity[0]) > 20:
                self.lot_quantity = 0.00

        if self.lot_min_quantity != 0.00:
            lot_min_quantity = str(self.lot_min_quantity).split('.')
            if len(lot_min_quantity[0]) > 15:
                self.lot_min_quantity = 0.00

        if self.lot_max_quantity != 0.00:
            lot_max_quantity = str(self.lot_max_quantity).split('.')
            if len(lot_max_quantity[0]) > 15:
                self.lot_max_quantity = 0.00
                        
class customer_details:
    def __init__(self):
        self.org_type: int = 0 # integer,
        self.org_name: str = None # character varying(2048) ,
        self.org_description: str  = None # character varying(255)
        self.org_email: str = None # character varying(100)
        self.org_address: str = None # character varying(250)
        self.org_state: str = None # character varying(100)
        self.org_country: str = None # character varying(2048)
        self.org_language: str = None # character varying(4)
        self.org_phone: str = None # character varying(22)
        self.org_fax: str = None # character varying(15)
        self.org_website: str = None # character varying(30)
        self.org_parent_id: int = 0 # integer DEFAULT 0,
        self.org_city: str = None # character varying(2048) COLLATE pg_catalog."default" DEFAULT 'NULL::character varying'::character varying,
        self.customer_nuts: str = None # character varying(2048) COLLATE pg_catalog."default",
        self.type_of_authority_code: str  = None #character varying(100) COLLATE pg_catalog."default",
        self.customer_main_activity : str= None # character varying(250) COLLATE pg_catalog."default",
        self.postal_code: str  = None #character varying(2048) COLLATE pg_catalog."default",
        self.contact_person: str = None #character varying(250);
       
    def customer_details_cleanup(self):
        if self.org_name == '':
            self.org_name = None
            
        if self.org_description == '':
            self.org_description = None
            
        if self.org_email == '':
            self.org_email = None
            
        if self.org_address == '':
            self.org_address = None
            
        if self.org_state == '':
            self.org_state = None
            
        if self.org_country == '':
            self.org_country = None
            
        if self.org_language == '':
            self.org_language = None
            
        if self.org_phone == '':
            self.org_phone = None
            
        if self.org_fax == '':
            self.org_fax = None
            
        if self.org_website == '':
            self.org_website = None
            
        if self.org_city == '':
            self.org_city = None
            
        if self.customer_nuts == '':
            self.customer_nuts = None
            
        if self.type_of_authority_code == '':
            self.type_of_authority_code = None
            
        if self.customer_main_activity == '':
            self.customer_main_activity = None
            
        if self.postal_code == '':
            self.postal_code = None
            
        if self.contact_person == '':
            self.contact_person = None
            
        if type(self.org_parent_id) is str:
            self.org_parent_id = int(self.org_parent_id)

        if self.org_name is not None:
            self.org_name = self.org_name[:2048].strip()
            
        if self.org_description is not None:
            self.org_description = self.org_description[:255].strip()
            
        if self.org_email is not None:
            self.org_email = self.org_email[:100].strip()
            validate = fn.valid_email(self.org_email)
            if validate is False:
                self.org_email = None
            
        if self.org_address is not None:
            self.org_address = self.org_address[:250].strip()
            
        if self.org_state is not None:
            self.org_state = self.org_state[:100].strip()
            
        if self.org_country is not None:
            self.org_country = self.org_country[:2048].strip()
            
        if self.org_language is not None:
            self.org_language = self.org_language[:4].strip()
            
        if self.org_phone is not None:
            self.org_phone = self.org_phone[:50].strip()
            
        if self.org_fax is not None:
            self.org_fax = self.org_fax[:50].strip()
            
        if self.org_website is not None:
            self.org_website = self.org_website[:2000].strip()
            
        if self.org_city is not None:
            self.org_city = self.org_city[:2048].strip()
            
        if self.customer_nuts is not None:
            self.customer_nuts = self.customer_nuts[:2048].strip()
            
        if self.type_of_authority_code is not None:
            self.type_of_authority_code = self.type_of_authority_code[:100].strip()
            
        if self.customer_main_activity is not None:
            self.customer_main_activity = self.customer_main_activity[:250].strip()
            
        if self.postal_code is not None:
            self.postal_code = self.postal_code[:2048].strip()
            
        if self.contact_person is not None:
            self.contact_person = self.contact_person[:250].strip()
       
class custom_tags:
    def __init__(self): 
        self.tender_custom_tag_tender_id: str = None     
        self.tender_custom_tag_description: str = None #  character varying(50),
        self.tender_custom_tag_value: str = None #  character varying(150),
        self.tender_custom_tag_company_id: str = None #  character varying(50),
       
    def custom_tags_cleanup(self):
        if self.tender_custom_tag_tender_id == '':
            self.tender_custom_tag_tender_id = None
            
        if self.tender_custom_tag_description == '':
            self.tender_custom_tag_description = None
            
        if self.tender_custom_tag_value == '':
            self.tender_custom_tag_value = None
            
        if self.tender_custom_tag_company_id == '':
            self.tender_custom_tag_company_id = None
            
        if self.tender_custom_tag_company_id is not None:
            self.tender_custom_tag_company_id = self.tender_custom_tag_company_id[:50].strip()
            
        if self.tender_custom_tag_description is not None:
            self.tender_custom_tag_description = self.tender_custom_tag_description[:50].strip()

        if self.tender_custom_tag_value is not None:
            self.tender_custom_tag_value = self.tender_custom_tag_value[:150].strip()
        
        if self.tender_custom_tag_tender_id is not None:
            self.tender_custom_tag_tender_id = self.tender_custom_tag_tender_id[:100].strip()

class tender:
    def __init__(self):
        self.tender_quantity: str = None
        self.is_publish_on_gec: bool = True
        self.is_publish_assumed: bool = False
        self.is_deadline_assumed: bool = False
        self.local_description: str = None
        self.related_tender_id: str = None
        self.cpv_at_source: str = None
        self.tender_id: str = None
        self.contract_type_actual: str = None
        self.notice_no: str = None # character varying(4000)
        self.notice_title: str = None # character varying(4000)
        self.main_language: str = None # character varying(2)
        self.performance_country = [] #character varying(4000) , class performance_country
        self.performance_state = [] #character varying(60), class performance_state
        self.est_amount: float = 0.00 #bigint,
        self.currency: str = None #character varying(100)',
        self.procurement_method: int = 2 # integer NOT NULL, Others = 2, ICB = 1 & NCB = 0
        self.eligibility: str = None #text COLLATE pg_catalog."default",
        self.notice_deadline: datetime = None # date,
        self.publish_date: datetime = None # date,
        self.script_name: str = None # character varying(10)
        self.document_fee: str  = None  #character varying(20)
        self.completed_steps: str = None  #character varying(20)
        self.crawled_at  = datetime.now() #timestamp without time zone,
        self.additional_source_name: str = None #character varying(250) COLLATE pg_catalog."default",
        self.additional_source_id: str = None #character varying(250) COLLATE pg_catalog."default",
        self.additional_tender_url: str = None #character varying(250) COLLATE pg_catalog."default",
        self.dispatch_date: datetime = None #timestamp without time zone,
        self.local_title: str = None #character varying(4000) COLLATE pg_catalog."default",
        self.grossbudgeteuro: float = 0.00 #numeric(20,2),
        self.netbudgeteuro: float = 0.00 #numeric(20,2),
        self.grossbudgetlc: float = 0.00 #numeric(20,2),
        self.netbudgetlc: float = 0.00 #numeric(20,2),
        self.vat: float = 0.00 #numeric(4,2),
        self.document_type_description: str = None #character varying(500) COLLATE pg_catalog."default",
        self.type_of_procedure: str = 'Other' #character varying(4000) COLLATE pg_catalog."default",
        self.type_of_procedure_actual: str = None #character varying(250) COLLATE pg_catalog."default",
        self.notice_summary_english: str = None #text COLLATE pg_catalog."default",
        self.identifier: str = None #character varying(4000) COLLATE pg_catalog."default",
        self.notice_type: int = 4 #integer,        
        self.cpvs = [] #class cpvs character varying(4000) COLLATE pg_catalog."default",
        self.contract_duration: str = None #character varying(500) COLLATE pg_catalog."default",
        self.project_name: str = None #character varying(500) COLLATE pg_catalog."default",
        self.document_cost:float = 0.00 #integer,
        self.earnest_money_deposit:str = None #character varying(500) COLLATE pg_catalog."default",
        self.document_purchase_start_time: date = None #date,
        self.document_purchase_end_time: date = None #date,
        self.pre_bid_meeting_date: date = None #date,
        self.document_opening_time: date = None #date,
        self.notice_contract_type: str = None #character varying(15)
        self.source_of_funds: str = "Own" #character varying(500) ,
        self.class_at_source: str = None #character varying(500),
        self.class_codes_at_source: str = None #character varying(500),
        self.class_title_at_source: str = None #character varying(500),
        self.bidding_response_method: str = 'Not Available' #character varying(50),
        self.notice_text: str = '' #text
        self.notice_url: str = None #character varying(4000),
        self.category: str = None #character varying(4000), class category
        self.tender_cancellation_date: datetime  = None
        self.tender_contract_end_date: datetime = None
        self.tender_contract_start_date: datetime = None
        self.tender_contract_number: str = None
        self.tender_is_canceled: bool = False
        self.tender_award_date: datetime  = None
        self.tender_min_quantity: float  = 0.00 #  numeric(15,2) DEFAULT 'NULL::numeric',
        self.tender_max_quantity: float  = 0.00 #  numeric(15,2) DEFAULT 'NULL::numeric',
        self.tender_quantity_uom: str  = None #character varying(50)
        self.is_lot_default: bool = False
        self.funding_agencies = [] #character varying(4000) class funding_agencies
        self.lot_details = [] #class lot_details
        self.custom_tags = [] #class custom_tags
        self.customer_details = [] #class customer_details
        self.tender_criteria = [] #class tender_criteria        
        self.attachments = [] #class attachments
   
    def tender_cleanup(self):
        global list_source_of_funds
        global list_class_at_source
        global list_notice_contract_type
        global list_notice_types
        global list_procurement_method
            
        if self.notice_summary_english == '':
            self.notice_summary_english = None
                
        if self.tender_quantity == '':
            self.tender_quantity = None
            
        if self.local_description == '':
            self.local_description = None
            
        if self.related_tender_id == '':
            self.related_tender_id = None
            
        if self.tender_id == '':
            self.tender_id = None
            
        if self.contract_type_actual == '':
            self.contract_type_actual = None
            
        if self.notice_no == '':
            self.notice_no = None
            
        if self.notice_title == '':
            self.notice_title = None
            
        if self.main_language == '':
            self.main_language = None
            
        if self.currency == '':
            self.currency = None
            
        if self.eligibility == '':
            self.eligibility = None
            
        if self.notice_deadline == '':
            self.notice_deadline = None
            
        if self.publish_date == '':
            self.publish_date = None
            
        if self.script_name == '':
            self.script_name = None
            
        if self.document_fee == '':
            self.document_fee = None
            
        if self.completed_steps == '':
            self.completed_steps = None
            
        if self.additional_source_name == '':
            self.additional_source_name = None
            
        if self.additional_source_id == '':
            self.additional_source_id = None
            
        if self.additional_tender_url == '':
            self.additional_tender_url = None
            
        if self.dispatch_date == '':
            self.dispatch_date = None
            
        if self.local_title == '':
            self.local_title = None
            
        if self.document_type_description == '':
            self.document_type_description = None
            
        if self.type_of_procedure_actual == '':
            self.type_of_procedure_actual = None
            
        if self.identifier == '':
            self.identifier = None
            
        if self.contract_duration == '':
            self.contract_duration = None
            
        if self.project_name == '':
            self.project_name = None
            
        if self.earnest_money_deposit == '':
            self.earnest_money_deposit = None
            
        if self.document_purchase_start_time == '':
            self.document_purchase_start_time = None
            
        if self.document_purchase_end_time == '':
            self.document_purchase_end_time = None
            
        if self.pre_bid_meeting_date == '':
            self.pre_bid_meeting_date = None
            
        if self.document_opening_time == '':
            self.document_opening_time = None
            
        if self.notice_contract_type == '':
            self.notice_contract_type = None
            
        if self.class_at_source == '':
            self.class_at_source = None
            
        if self.class_codes_at_source == '':
            self.class_codes_at_source = None
            
        if self.class_title_at_source == '':
            self.class_title_at_source = None
            
        if self.notice_url == '':
            self.notice_url = None
            
        if self.category == '':
            self.category = None
            
        if self.tender_cancellation_date == '':
            self.tender_cancellation_date = None
            
        if self.tender_contract_end_date == '':
            self.tender_contract_end_date = None
            
        if self.tender_contract_start_date == '':
            self.tender_contract_start_date = None
            
        if self.tender_contract_number == '':
            self.tender_contract_number = None
            
        if self.tender_award_date == '':
            self.tender_award_date = None
            
        if self.tender_quantity_uom == '':
            self.tender_quantity_uom = None

        if self.tender_quantity is not None:
            self.tender_quantity = self.tender_quantity[:50].strip()

        if self.notice_no is not None:
            self.notice_no = self.notice_no[:100].strip()
                
        if self.related_tender_id is not None:
            self.related_tender_id = self.related_tender_id[:100].strip()
                
        if self.contract_type_actual is not None:
            self.contract_type_actual = self.contract_type_actual[:500].strip()

        if self.cpv_at_source == '':
            self.cpv_at_source = None
                
        if self.cpv_at_source is not None:
            cpv_at_source_unique = self.cpv_at_source.split(',')
            cpv_at_source_unique_list = list(dict.fromkeys(cpv_at_source_unique))
        
            cpv_at_source = ''
            for cpv in cpv_at_source_unique_list:
                cpv_at_source += cpv 
                cpv_at_source += ',' 
            self.cpv_at_source = cpv_at_source.rstrip(',')
                
        if self.tender_id is not None:
            self.tender_id = self.tender_id[:100].strip()
            
        if self.local_title is not None:
            self.local_title = self.local_title[:4000].strip()

        if self.main_language is not None:
            self.main_language = self.main_language[:2].strip()

        if type(self.est_amount) is float:
            self.est_amount = float("%.2f" % self.est_amount)
        elif type(self.est_amount) is int:
            self.est_amount = float(self.est_amount)
        else:
            self.est_amount = 0.00

        if self.currency is not None:
            self.currency = self.currency[:3].strip()

        if self.script_name is not None:
            self.script_name = self.script_name[:50].strip()

        if self.document_fee is not None:
            self.document_fee = self.document_fee[:200].strip()

        if self.completed_steps is not None:
            self.completed_steps = self.completed_steps[:200].strip()

        if self.additional_source_name is not None:
            self.additional_source_name = self.additional_source_name[:50].strip()

        if self.additional_source_id is not None:
            self.additional_source_id = self.additional_source_id[:100].strip()

        if self.additional_tender_url is not None:
            self.additional_tender_url = self.additional_tender_url[:1000].strip()

        if type(self.grossbudgeteuro) is float:
            self.grossbudgeteuro = float("%.2f" % self.grossbudgeteuro)
        elif type(self.grossbudgeteuro) is int:
            self.grossbudgeteuro = float(self.grossbudgeteuro)
        else:
            self.grossbudgeteuro = 0.00

        if type(self.netbudgeteuro) is float:
            self.netbudgeteuro = float("%.2f" % self.netbudgeteuro)
        elif type(self.netbudgeteuro) is int:
            self.netbudgeteuro = float(self.netbudgeteuro)
        else:
            self.netbudgeteuro = 0.00

        if type(self.grossbudgetlc) is float:
            self.grossbudgetlc = float("%.2f" % self.grossbudgetlc)
        elif type(self.grossbudgetlc) is int:
            self.grossbudgetlc = float(self.grossbudgetlc)
        else:
            self.grossbudgetlc = 0.00

        if type(self.netbudgetlc) is float:
            self.netbudgetlc = float("%.2f" % self.netbudgetlc)
        elif type(self.netbudgetlc) is int:
            self.netbudgetlc = float(self.netbudgetlc)
        else:
            self.netbudgetlc = 0.00

        if type(self.vat) is float:
            self.vat = float("%.2f" % self.vat)
        elif type(self.vat) is int:
            self.vat = float(self.vat)
        else:
            self.vat = 0.00


        if self.document_type_description is not None:
            self.document_type_description = self.document_type_description[:500].strip()

        if self.type_of_procedure is not None:
            self.type_of_procedure = self.type_of_procedure[:100].strip()

        if self.type_of_procedure_actual is not None:
            self.type_of_procedure_actual = self.type_of_procedure_actual[:500].strip()

        if self.identifier is not None:
            self.identifier = self.identifier[:4000].strip()

        if self.contract_duration is not None:
            self.contract_duration = self.contract_duration[:500].strip()

        if self.project_name is not None:
            self.project_name = self.project_name[:500].strip()
        
        if type(self.document_cost) is float:
            self.document_cost = float("%.2f" % self.document_cost)
        elif type(self.document_cost) is int:
            self.document_cost = float(self.document_cost)
        else:
            self.document_cost = 0.00

        if self.earnest_money_deposit is not None:
            self.earnest_money_deposit = self.earnest_money_deposit[:500].strip()

        if type(self.document_purchase_start_time) is str:
            self.document_purchase_start_time = datetime.strptime(self.document_purchase_start_time, '%Y/%m/%d').date()

        if self.document_purchase_start_time is not None:
            self.document_purchase_start_time = fn.date(str(self.document_purchase_start_time))
            
        if type(self.document_purchase_end_time) is str:
            self.document_purchase_end_time = datetime.strptime(self.document_purchase_end_time, '%Y/%m/%d').date()

        if self.document_purchase_end_time is not None:
            self.document_purchase_end_time = fn.date(str(self.document_purchase_end_time))
            
        if type(self.pre_bid_meeting_date) is str:
            self.pre_bid_meeting_date = datetime.strptime(self.pre_bid_meeting_date, '%Y/%m/%d').date()

        if self.pre_bid_meeting_date is not None:
            self.pre_bid_meeting_date = fn.date(str(self.pre_bid_meeting_date))

        if self.document_opening_time is not None:
            self.document_opening_time = fn.date(str(self.document_opening_time))
            
        if self.notice_contract_type is not None:
            self.notice_contract_type = self.notice_contract_type[:15].strip()

        if self.class_at_source is not None:
            self.class_at_source = self.class_at_source[:500].strip()
            
        if self.source_of_funds is not None:
            self.source_of_funds = self.source_of_funds[:500].strip()

        if self.class_codes_at_source is not None:
            self.class_codes_at_source = self.class_codes_at_source[:500].strip()

        if self.class_title_at_source is not None:
            self.class_title_at_source = self.class_title_at_source[:1000].strip()

        if self.notice_url is not None:
            self.notice_url = self.notice_url[:2000].strip()
            
        if self.bidding_response_method is not None:
            self.bidding_response_method = self.bidding_response_method[:50].strip()

        if self.category is not None:
            self.category = self.category.strip()
                
        if self.cpvs != []:
            for cpv in self.cpvs:
                if cpv.cpv_code not in main_cpv_list.cpv_list:
                    self.cpvs = []
                
        if (self.cpvs == [] and self.notice_title is not None) or (self.cpvs == [''] and self.notice_title is not None):
            cpv_list = fn.assign_cpvs_from_title(self.notice_title.lower(), self.category)
            for cpv in cpv_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv
                self.cpvs.append(cpvs_data)

        if self.notice_title is not None:
            self.notice_title = self.notice_title.title()
            self.notice_title = self.notice_title[:4000].strip()
            
        if self.source_of_funds not in list_source_of_funds:
            self.source_of_funds = "Own"
            
        if self.procurement_method not in list_procurement_method:
            self.procurement_method = 2
            
        if self.class_at_source not in list_class_at_source:     
            self.class_at_source = 'OTHERS'
            
        if self.notice_type not in list_notice_types:     
            self.notice_type = 4
        
        if self.type_of_procedure not in list_of_procedure:
            self.type_of_procedure = 'Other'
                
        if self.notice_contract_type not in list_notice_contract_type:
            self.notice_contract_type = None

        if self.notice_deadline is not None:
            self.notice_deadline = fn.date(str(self.notice_deadline))
            
        if self.publish_date is None and self.notice_deadline is not None:
            self.publish_date = date.today().strftime('%Y/%m/%d %H:%M:%S')   
            self.is_publish_assumed = True
        if self.publish_date is not None:
            try:
                self.publish_date = datetime.strptime(self.publish_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.publish_date = fn.date(str(self.publish_date))
            
        
        if self.dispatch_date is not None:
            try:
                self.dispatch_date = datetime.strptime(self.dispatch_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.dispatch_date = fn.date(str(self.dispatch_date))
        
        if (self.notice_deadline is None or self.notice_deadline == '') and self.publish_date is not None:
            if self.notice_type == 2 or self.notice_type == 3:
                self.notice_deadline = (datetime.strptime(self.publish_date, '%Y/%m/%d %H:%M:%S') + timedelta(365)).strftime('%Y/%m/%d %H:%M:%S')
                self.is_deadline_assumed = True
            elif self.notice_type != 7:
                self.notice_deadline = (datetime.strptime(self.publish_date, '%Y/%m/%d %H:%M:%S') + timedelta(15)).strftime('%Y/%m/%d %H:%M:%S')
                self.is_deadline_assumed = True
                    

        if self.notice_url is not None:
            validation = fn.url_match(self.notice_url)
            if validation is False:
                self.notice_url = None
                    
        if self.additional_tender_url is not None:
            validation = fn.url_match(self.additional_tender_url)
            if validation is False:
                self.additional_tender_url = None
                    
        if self.document_type_description is None and self.notice_type == 0:
            self.document_type_description = 'Others'
        
        if self.document_type_description is None and self.notice_type == 1:
            self.document_type_description = 'Procurement News'
        
        if self.document_type_description is None and self.notice_type == 2:
            self.document_type_description = 'Prior Information Notice'
        
        if self.document_type_description is None and self.notice_type == 3:
            self.document_type_description = 'Procurement Plan'
        
        if self.document_type_description is None and self.notice_type == 4:
            self.document_type_description = 'Invitation for Bids/Request for Proposal/Request for bid'
        
        if self.document_type_description is None and self.notice_type == 5:
            self.document_type_description = 'Request For Expressions of Interest'
        
        if self.document_type_description is None and self.notice_type == 6:
            self.document_type_description = 'Prequalification Notice'
        
        if self.document_type_description is None and self.notice_type == 7:
            self.document_type_description = 'Contract awards'
        
        if self.document_type_description is None and self.notice_type == 8:
            self.document_type_description = 'Request for Public Consultations'
        
        if self.document_type_description is None and self.notice_type == 9:
            self.document_type_description = 'Auction'
        
        if self.document_type_description is None and self.notice_type == 10:
            self.document_type_description = 'Project'
        
        if self.document_type_description is None and self.notice_type == 11:
            self.document_type_description = 'Vacancy'
        
        if self.document_type_description is None and self.notice_type == 12:
            self.document_type_description = 'Grants'
        
        if self.document_type_description is None and self.notice_type == 13:
            self.document_type_description = 'Acquisition'
        
        if self.document_type_description is None and self.notice_type == 14:
            self.document_type_description = 'Merger'
        
        if self.document_type_description is None and self.notice_type == 15:
            self.document_type_description = 'Reports'
        
        if self.document_type_description is None and self.notice_type == 16:
            self.document_type_description = 'Amendment'
                
        if self.tender_criteria != []:
            for tender_criteria in self.tender_criteria:
                if tender_criteria.tender_criteria_title is None:
                    self.tender_criteria = []
        
        if self.tender_cancellation_date is not None:
            try:
                self.tender_cancellation_date = datetime.strptime(self.tender_cancellation_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.tender_cancellation_date = fn.date(str(self.tender_cancellation_date))
        
        if self.tender_contract_end_date is not None:
            try:
                self.tender_contract_end_date = datetime.strptime(self.tender_contract_end_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.tender_contract_end_date = fn.date(str(self.tender_contract_end_date))
        
        if self.tender_contract_start_date is not None:
            try:
                self.tender_contract_start_date = datetime.strptime(self.tender_contract_start_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.tender_contract_start_date = fn.date(str(self.tender_contract_start_date))
        
        if self.tender_contract_number is not None:
            self.tender_contract_number = self.tender_contract_number[:100].strip()
        
        if self.tender_award_date is not None:
            try:
                self.tender_award_date = datetime.strptime(self.tender_award_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
            self.tender_award_date = fn.date(str(self.tender_award_date))
        
        if type(self.tender_max_quantity) is float:
            self.tender_max_quantity = float("%.2f" % self.tender_max_quantity)
        elif type(self.tender_max_quantity) is int:
            self.tender_max_quantity = float(self.tender_max_quantity)
        else:
            self.tender_max_quantity = 0.00

        if type(self.tender_min_quantity) is float:
            self.tender_min_quantity = float("%.2f" % self.tender_min_quantity)
        elif type(self.tender_min_quantity) is int:
            self.tender_min_quantity = float(self.tender_min_quantity)
        else:
            self.tender_min_quantity = 0.00
        
        if self.tender_quantity_uom is not None:
            self.tender_quantity_uom = self.tender_quantity_uom[:50].strip()
                
        if self.est_amount == 0.00:
            self.est_amount = self.grossbudgetlc
        if self.est_amount == 0.00:
            self.est_amount = self.grossbudgeteuro
        if self.est_amount == 0.00:
            self.est_amount = self.netbudgetlc
        if self.est_amount == 0.00:
            self.est_amount = self.netbudgeteuro
        if self.cpvs != []:
            self.cpvs = list({v.cpv_code:v for v in self.cpvs}.values())
        if self.attachments != []:
            self.attachments = list({url.external_url:url for url in self.attachments}.values())
            
        if self.grossbudgeteuro != 0.00:
            grossbudgeteuro = str(self.grossbudgeteuro).split('.')
            if len(grossbudgeteuro[0]) > 20:
                self.grossbudgeteuro = 0.00

        if self.est_amount != 0.00:
            est_amount = str(self.est_amount).split('.')
            if len(est_amount[0]) > 20:
                self.est_amount = 0.00

        if self.netbudgeteuro != 0.00:
            netbudgeteuro = str(self.netbudgeteuro).split('.')
            if len(netbudgeteuro[0]) > 20:
                self.netbudgeteuro = 0.00

        if self.grossbudgetlc != 0.00:
            grossbudgetlc = str(self.grossbudgetlc).split('.')
            if len(grossbudgetlc[0]) > 20:
                self.grossbudgetlc = 0.00

        if self.netbudgetlc != 0.00:
            netbudgetlc = str(self.netbudgetlc).split('.')
            if len(netbudgetlc[0]) > 20:
                self.netbudgetlc = 0.00

        if self.vat != 0.00:
            vat = str(self.vat).split('.')
            if len(vat[0]) > 20:
                self.vat = 0.00

        if self.document_cost != 0.00:
            document_cost = str(self.document_cost).split('.')
            if len(document_cost[0]) > 20:
                self.document_cost = 0.00

        if self.tender_max_quantity != 0.00:
            tender_max_quantity = str(self.tender_max_quantity).split('.')
            if len(tender_max_quantity[0]) > 15:
                self.tender_max_quantity = 0.00

        if self.tender_min_quantity != 0.00:
            tender_min_quantity = str(self.tender_min_quantity).split('.')
            if len(tender_min_quantity[0]) > 15:
                self.tender_min_quantity = 0.00
                
class cross_check_output:
    def __init__(self):
        self.notice_no: str = None # character varying(4000)
        self.notice_deadline: datetime = None # date,
        self.publish_date: datetime = None # date,
        self.script_name: str = None # character varying(10)
        self.crawled_at  = datetime.now() #timestamp without time zone,
        self.local_title: str = None #character varying(4000) COLLATE pg_catalog."default",
        self.notice_type: int = 4 #integer,
        self.notice_url: str = None #character varying(4000),
        self.method_name: str = None #character varying(4000),
