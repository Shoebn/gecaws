import os
import uuid
from datetime import date, datetime, timedelta
import re
import sys

class awardCriteria:
    def __init__(self):
        self.title: str = None 
        self.weight: int = None 
        self.isPriceRelated: str = None 
            
    def awardCriteria_cleanup(self):
        if self.title is None:
            self.title = 'Price'
            self.weight = 100
            self.isPriceRelated = True
        if self.title is not None and self.weight is None:
            self.weight = 100
        
class customer:
    def __init__(self):
        self.name: str = None 
        self.country: str = None  
        self.city: str = None 
        self.street: str = None 
        self.postalCode: str = None 
        self.email: str = None 
        self.phone: str = None 
        self.nuts: str = None 
        self.typeOfAuthorityCode: str = None 
        self.mainActivity: str = None 
        
class awardDetails:
    def __init__(self):
        self.awardWinner: str = None 
        self.awardWinnerGroupName: str = None 
        self.grossBudgetEuro: float = 0.00
        self.netBudgetEuro: float = 0.00
        self.grossBudgetLC:float = 0.00 
        self.netBudgetLC: float = 0.00
        self.quantity: float = 0.00 
        self.notes:  str = None
        
    def awardDetails_cleanup(self):
        if self.grossBudgetEuro is not None :
            self.grossBudgetEuro = float(self.grossBudgetEuro)
        if self.netBudgetEuro is not None :
            self.netBudgetEuro = float(self.netBudgetEuro)
        if self.grossBudgetLC is not None :
            self.grossBudgetLC = float(self.grossBudgetLC)
        if self.netBudgetLC is not None :
            self.netBudgetLC = float(self.netBudgetLC)
        if self.quantity is not None :
            self.quantity = float(self.quantity)
    
class lotCPVCodes:
    def __init__(self):
        self.lotCPVCodes: str = None

class tenderCPVCodes:
    def __init__(self):
        self.tenderCPVCodes: str = None         
        
class lots:
    def __init__(self):
        self.actualNumber: str = None
        self.number: str = None 
        self.title: str  = None 
        self.description: str = None
        self.grossBudgetEuro: float  = 0.00 
        self.netBudgetEuro: float  = 0.00
        self.grossBudgetLC: float  = 0.00
        self.netBudgetLC: float  = 0.00
        self.vat: float  = 0.00
        self.quantity: float = 0.00
        self.minQuantity: float  = 0.00
        self.maxQuantity: float  = 0.00
        self.quantityUOM: str  = None
        self.contractNumber: str  = None
        self.contractDuration: int  = None 
        self.contractStartDate: datetime = None
        self.contractEndDate: datetime  = None 
        self.lotNuts: str  = None 
        self.isCanceled: bit = None 
        self.cancellationDate: date  = None 
        self.lotAwardDate: date  = None 
        self.lotCPVCodes = ''
        self.contractType: str = None
        self.awardCriteria = [] 
        self.awardDetails = []
        
    def lots_cleanup(self):
        if self.grossBudgetEuro is not None :
            self.grossBudgetEuro = float(self.grossBudgetEuro)
        if self.netBudgetEuro is not None :
            self.netBudgetEuro = float(self.netBudgetEuro)
        if self.grossBudgetLC is not None :
            self.grossBudgetLC = float(self.grossBudgetLC)
        if self.netBudgetLC is not None :
            self.netBudgetLC = float(self.netBudgetLC)
        if self.quantity is not None :
            self.quantity = float(self.quantity)
        if self.vat is not None :
            self.vat = float(self.vat)
        if self.minQuantity is not None :
            self.minQuantity = float(self.minQuantity)
        if self.maxQuantity is not None :
            self.maxQuantity = float(self.maxQuantity)
        if self.awardCriteria == [] :
            awardCriteria_data = awardCriteria()
            awardCriteria_data.title = 'Price'
            awardCriteria_data.weight = 100
            awardCriteria_data.isPriceRelated = True
            self.awardCriteria.append(awardCriteria_data)
            
class attachments:
    def __init__(self):        
        self.description: str = None  
        self.url: str = None
        self.size: float = 0.00 
    def attachments_cleanup(self):
        if self.size is not None :
            self.size = float(self.size)


class customTags:
    def __init__(self):
        self.description: str = None 
        self.value: str = None 
        self.companyId: int = None 
        
class country:
    def __init__(self):
        self.country: str = None         
        
class tender:
    def __init__(self):
        self.localDescription: str = None
        self.crawledAt: datetime = None 
        self.sourceName: str = None
        self.tenderId: str = None  
        self.relatedTenderId: str = None  
        self.additionalSourceName:  str = None
        self.additionalSourceId:  str = None
        self.dispatchDate:  datetime = None
        self.publicationDate:  date = None
        self.submissionDeadline: datetime = None 
        self.documentType: str = None 
        self.documentTypeDescription: str = None 
        self.typeOfProcedure:  str = None
        self.typeOfProcedureActual:  str = None 
        self.title:  str = None
        self.localTitle:str = None  
        self.description:str = None  
        self.grossBudgetEuro:  float = 0.00
        self.netBudgetEuro:  float = 0.00
        self.grossBudgetLC:  float = 0.00
        self.netBudgetLC:   float = 0.00
        self.vat:  float = 0.00
        self.tenderURL: str = None 
        self.additionalTenderURL: str = None 
        self.currency:str = None  
        self.country = ''
        self.language:str = None  
        self.tenderCPVCodes = ''
        self.identifier: str = None
        self.htmlBody: str = '' 
        self.customer= []
        self.lots=[]
        self.awardCriteria= []
        self.attachments=  []
        self.customTags=  []
        
    def tender_cleanup(self):
        if self.grossBudgetEuro is not None :
            self.grossBudgetEuro = float(self.grossBudgetEuro)
        if self.netBudgetEuro is not None :
            self.netBudgetEuro = float(self.netBudgetEuro)
        if self.grossBudgetLC is not None :
            self.grossBudgetLC = float(self.grossBudgetLC)
        if self.netBudgetLC is not None :
            self.netBudgetLC = float(self.netBudgetLC)
        if self.vat is not None :
            self.vat = float(self.vat)
        if self.awardCriteria == [] :
            awardCriteria_data = awardCriteria()
            awardCriteria_data.title = 'Price'
            awardCriteria_data.weight = 100
            awardCriteria_data.isPriceRelated = True
            self.awardCriteria.append(awardCriteria_data)
