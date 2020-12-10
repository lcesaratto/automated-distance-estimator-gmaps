import pandas as pd
# import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
import time
import re
import os

def save_new_entry(df_row):  
    df_all = pd.read_csv("all_entries.csv")
    df_all = df_all.append(df_row[['von Str.','von Ort','von PLZ','nach Str.','nach Ort','nach PLZ','Kilometer']],ignore_index=True)
    df_all.to_csv("all_entries.csv",index=False)

def estimate_kilometers(row):
    df_all = pd.read_csv("all_entries.csv")

    value = df_all.loc[(df_all["von Str."] == row["von Str."]) & (df_all["nach Str."] == row["nach Str."])]["Kilometer"]
    
    if not value.empty:
        return float(value.values)
    
    try:
        von = ' '.join(filter(None, [row["von PLZ"],row["von Ort"]]))
        nach = ' '.join(filter(None, [row["nach PLZ"],row["nach Ort"]]))
        url = ("https://www.google.de/maps/dir/?api=1"+
        "&origin="+', '.join(filter(None, [row["von Str."],von]))+
        "&destination="+', '.join(filter(None, [row["nach Str."],nach]))+
        "&travelmode=bicycling").replace(" ", "+")
        # print(url)

        options = Options()
        options.add_argument("--lang=de")
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        # driver.minimize_window()
        driver.get(url)
        # wait = WebDriverWait(driver, 10)
        # menu_bt = wait.until(EC.element_to_be_clickable(
        #                     (By.XPATH, '//button[@id=\'introAgreeButton\']'))
        #                 )  
        # menu_bt.click()
        time.sleep(5)
        response = BeautifulSoup(driver.page_source, 'html.parser')

        r = response.find('div', class_='section-directions-trip clearfix selected')
        kms = r.find('div', class_='section-directions-trip-distance section-directions-trip-secondary-text').text
        unit = re.sub('[^a-z]','',kms)
        kms = re.sub('[^0-9,]','',kms)
        kms = float(re.sub('[,]','.',kms))
        if unit == 'm':
            kms /= 1000

        # rlist = response.find_all('div', class_='section-directions-trip clearfix')
        # for r in rlist:
        #     kms_add = r.find('div', class_='section-directions-trip-distance section-directions-trip-secondary-text').text
        
        driver.quit()
        df_dict = {'von Str.':[row['von Str.']],'von Ort':[row['von Ort']],
                    'von PLZ':[row['von PLZ']],'nach Str.':[row['nach Str.']],
                    'nach Ort':[row['nach Ort']],'nach PLZ':[row['nach PLZ']],
                    'Kilometer':[kms]}
        save_new_entry(pd.DataFrame.from_dict(df_dict))
        return float(kms)
    except Exception as e:
        print(e)
        return float('NaN')

if not os.path.isfile('all_entries.csv'):
    newDF = pd.DataFrame(columns=['von Str.','von Ort','von PLZ','nach Str.','nach Ort','nach PLZ','Kilometer'])
    newDF.to_csv('all_entries.csv',index=False)

df = pd.read_excel('Denise_Poehl-Oktober_November.xlsx')
df.fillna('', inplace=True)
df = df.astype({'Datum': 'str','von Str.': 'str','von Ort': 'str','von PLZ': 'str',
            'nach Str.': 'str','nach Ort': 'str','nach PLZ': 'str'})
df["von PLZ"] = df["von PLZ"].apply(lambda x:x.split('.',1)[0])
df["nach PLZ"] = df["nach PLZ"].apply(lambda x:x.split('.',1)[0])

df["Kilometer"] = df.apply(estimate_kilometers,axis=1)

df.to_excel('Denise_Poehl-Oktober_November.xlsx',index=False)
print(df.head(60))