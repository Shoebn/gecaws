import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('omw-1.4')
from nltk.corpus import wordnet
from fuzzywuzzy import process
import pickle
import pandas as pd
from gec_common.web_application_properties import *

import ml.cpvdict as main_cpvdict

# Loading Appropirate models for division

# if no category specified
file = open(ASSETS_PATH  + 'ml/models/india/india_division.pickle', 'rb')
division_cv1 = pickle.load(file)
division_clf = pickle.load(file)

#if Category specified as goods or services
file = open(ASSETS_PATH  + 'ml/models/india/india_goods_division.pickle', 'rb')
goods_division_cv1 = pickle.load(file)
goods_division_clf = pickle.load(file)

file = open(ASSETS_PATH  + 'ml/models/india/india_services_division.pickle', 'rb')
services_division_cv1 = pickle.load(file)
services_division_clf = pickle.load(file)


# Loading appropriate models for classes

# if no category specified
file = open(ASSETS_PATH  + 'ml/models/india/india_class.pickle', 'rb')
class_cv1 = pickle.load(file)
class_clf = pickle.load(file)

# For specific category
file = open(ASSETS_PATH  + 'ml/models/india/india_goods_class.pickle', 'rb')
goods_class_cv1 = pickle.load(file)
goods_class_clf = pickle.load(file)

file = open(ASSETS_PATH  + 'ml/models/india/india_works_class.pickle', 'rb')
works_class_cv1 = pickle.load(file)
works_class_clf = pickle.load(file)

file = open(ASSETS_PATH  + 'ml/models/india/india_services_class.pickle', 'rb')
services_class_cv1 = pickle.load(file)
services_class_clf = pickle.load(file)


def cpv_dict():
    return main_cpvdict.cpvdict

cpv_dict = cpv_dict()


word_bag = ['procurement', 'services', 'provision',
            'quarterly', 'department', 'jessore', 'university', 'purchase', 'image',
            'agreement', 'rfq', 'materials', 'acquisition', 'goods', 'purchases',
            'agency', 'needs', 'state', 'appliances', 'tajikistan', 'government',
            'republic', 'emergency','spares', 'general','design services',
            'support', 'supports', 'work', 'contract', 'contracting',
            'infrastructure', 'sector', 'sectors', 'execution', 'installation', 'improvement',
            'system', 'expansion', 'program', 'class', 'different', 'instruments', 'instrument',
            'works', 'type', 'right', 'needs', 'item', 'equipment', 'supply', 'agency',
            'local', 'local e-tender', 'accessories',
            'e-tender', 'management services', 'removal services', 'accessories',
            'control services', 'management system',
            'service provider', 'maintenance services', 'service', 'machine',
            'collection', 'consultancy services', 'consultancy service',
            'distribution', 'maintenance', 'maintenance work','maintenance works',
            'consultancy', 'terminal', 'miscellaneous', 'installation work', 'support services'
            ]


def unique(list1):
    unique_list = []
    for x in list1:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list


def generate_tagged_keyword_sentence(title):

    keywords = []
    tokens = nltk.word_tokenize(title)
    tagged = nltk.pos_tag(tokens)

    for i in range(0, len(tagged)):

        if (wordnet.synsets(tagged[i][0])):

            if (tagged[i][1] == 'NNP' or tagged[i][1] == 'NNPS' or tagged[i][1] == 'NNS' or tagged[i][
                1] == 'NN'):
                if (tagged[i - 1][1] == 'IN'):
                    keywords.append(tagged[i][0])
                if (tagged[i - 1][1] == 'JJ'):
                    if (tagged[i - 2][1] == 'IN' or tagged[i - 2][1] == 'CC'):
                        keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0])
                    else:
                        keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0])
                    keywords.append(tagged[i - 1][0])
                if (tagged[i - 1][1] == 'VBG'):
                    keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0])
                if (tagged[i - 1][1] == 'NN' or tagged[i - 1][1] == 'NNS'):
                    keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0])
                keywords.append(tagged[i][0])

    #print(keywords)
    #print('')
    keywords = unique(keywords)
    title = " ".join(keywords)
    return title


def tag_cpvs(keywords):

    cpv_list = []

    if (len(keywords) == 1):

        common_words = ['supply', 'service', 'services', 'material',
                        'materials', 'apparatus', 'equipment',
                        'equipments', 'supplies', 'maintenance', 'improvement',
                        'development', 'repair', 'goods'
                        ]
        if (keywords[0] in common_words):
            return cpv_list

    try:
        i = 0

        small_words = ['tea', 'oil', 'air', 'lot', 'ups','gun','vhf']
        keywords = [s for s in keywords if (len(s) > 3 or s in small_words)]
        data = []
        if (len(keywords) > 0):
            for keyword in keywords:
                for title in cpv_dict:
                    dict_title = cpv_dict.get(title)
                    if keyword in dict_title:
                        data.append(dict_title)

            choices = []
            for row in data:
                choices.append(row[0].lower())

            #print(choices)
            #print('')

            cpv_titles = []

            for keyword in keywords:

                options = process.extract(keyword, choices, limit=2)

                #print(options)

                for i in range(0, len(options)):
                    if (options[i][1] >= 92):
                        cpv_titles.append(options[i][0])
                        #if (options[i][1] > 98):
                         #   break
            if (len(cpv_titles) > 0):

                for cpv_title in cpv_titles:
                    cpv_list.append(cpv_dict[cpv_title])

                return cpv_list
            else:
                return cpv_list
        else:
            return cpv_list
    except:
        return cpv_list



def division_cpv(title_series, category = False):

    if(category):
        if(category=='services'):
            title_class_cv = services_division_cv1.transform(title_series.values.astype('U'))
            cpv_division = services_division_clf.predict(title_class_cv[0])[0]
        elif(category=='goods'):
            title_class_cv = goods_division_cv1.transform(title_series.values.astype('U'))
            cpv_division = goods_division_clf.predict(title_class_cv[0])[0]
        #print(division_clf.predict_proba(title_class_cv[0]))
        #print(division_clf.predict_proba(title_class_cv[0])[0][0]*100)
        else:
            title_class_cv = division_cv1.transform(title_series.values.astype('U'))
            cpv_division = division_clf.predict(title_class_cv[0])[0]
    else:
        title_class_cv = division_cv1.transform(title_series.values.astype('U'))
        cpv_division = division_clf.predict(title_class_cv[0])[0]

    return str(cpv_division)

def class_cpv(title_series, category = False):

    if(category):
        if(category=='goods'):
            # This classifier needs to be changed once we have goods classifier
            title_class_cv = goods_class_cv1.transform(title_series.values.astype('U'))
            cpv_class = goods_class_clf.predict(title_class_cv[0])[0]
        elif(category=='works'):
            title_class_cv = works_class_cv1.transform(title_series.values.astype('U'))
            cpv_class = works_class_clf.predict(title_class_cv[0])[0]
        elif(category=='services'):
            title_class_cv = services_class_cv1.transform(title_series.values.astype('U'))
            cpv_class = services_class_clf.predict(title_class_cv[0])[0]
        else:
            title_class_cv = class_cv1.transform(title_series.values.astype('U'))
            cpv_class = class_clf.predict(title_class_cv[0])[0]
    else:
        title_class_cv = class_cv1.transform(title_series.values.astype('U'))
        cpv_class = class_clf.predict(title_class_cv[0])[0]

    return str(cpv_class)



def get_cpvs(sentence, category= False):

    cpvs = []
    keywords = []
    sentence = sentence.lower()
    tokens = nltk.word_tokenize(sentence)
    tagged = nltk.pos_tag(tokens)
    dict_sentence = ''

    for i in range(0, len(tagged)):

        if (wordnet.synsets(tagged[i][0])):
            dict_sentence += tagged[i][0] + ' '

        if (tagged[i][1] == 'NNP' or tagged[i][1] == 'NNPS' or tagged[i][1] == 'NNS' or tagged[i][1] == 'NN'):
            if (tagged[i - 1][1] == 'IN'):
                keywords.append(tagged[i][0].lower())
            if (tagged[i - 1][1] == 'JJ'):
                if (tagged[i - 2][1] == 'IN' or tagged[i - 2][1] == 'CC'):
                    keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0].lower())
                else:
                    keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0])
                keywords.append(tagged[i - 1][0])
            if (tagged[i - 1][1] == 'VBG'):
                keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0])
            if (tagged[i - 1][1] == 'NN' or tagged[i - 1][1] == 'NNS'):
                keywords.append(tagged[i - 1][0] + ' ' + tagged[i][0])
            keywords.append(tagged[i][0])

    # Stemming can be done here.. on first e.
    keywords_new = [e for e in keywords if e not in (word_bag)]

    keywords_new = unique(keywords_new)
    keywords_new = keywords_new[:15]

    #print(keywords_new)

    if (len(keywords_new) < 16 and len(keywords_new) > 0):
        cpvs = tag_cpvs(keywords_new)

    if cpvs == []:


        title_series = pd.Series(dict_sentence)

        if(category):
            if(category=='works'):
                division = '45000000'
                clss = class_cpv(title_series, category)
            else:
                division = division_cpv(title_series, category)
                clss = class_cpv(title_series, category)
        else:

            division = division_cpv(title_series)
            clss = class_cpv(title_series)

        #print(division)
        if(len(division)==7):
            division = '0'+division

        if (len(clss) == 7):
            clss = '0' + clss

        cpvs.insert(0,division)
        if(division[:2]== clss[:2]):
            cpvs.insert(1, clss)

    cpvs = unique(cpvs)

    #print(cpvs)

    #correct_cpvs = []

    #for cpv in cpvs:
     #   if(cpv[:2]== cpvs[0][:2]):
      #      correct_cpvs.append(cpv)

    #print(correct_cpvs)

    return cpvs
