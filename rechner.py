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

def convert_kms(kms):
    unit = re.sub('[^a-z]','',kms)
    kms = re.sub('[^0-9,]','',kms)
    kms = float(re.sub('[,]','.',kms))
    if unit == 'm':
        kms /= 1000
    return kms

def estimate_kilometers(row,travel_mode):
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
        "&travelmode="+travel_mode).replace(" ", "+")
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
        kms = convert_kms(kms)

        r_list = response.find_all('div', class_='section-directions-trip clearfix')
        for r_add in r_list:
            kms_add = r_add.find('div', class_='section-directions-trip-distance section-directions-trip-secondary-text').text
            kms_add = convert_kms(kms_add)
            if kms_add < kms:
                kms = kms_add
        
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

def calculate_daily_sum(df):
    last_index = 0
    partial_sum = 0
    for index, row in df.iterrows():
        if row['Datum'] != '':
            df.at[last_index,'Kilometer ges./Tag'] = partial_sum
            last_index = index
            partial_sum = row['Kilometer']
        elif row['Datum'] == '':
            partial_sum += row['Kilometer']
        if index==df.last_valid_index():
            df.at[last_index,'Kilometer ges./Tag'] = partial_sum
    return df

def check_entries_df():
    if not os.path.isfile('all_entries.csv'):
        newDF = pd.DataFrame(columns=['von Str.','von Ort','von PLZ','nach Str.','nach Ort','nach PLZ','Kilometer'])
        newDF.to_csv('all_entries.csv',index=False)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        import sys
        import os
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    check_entries_df()
    with open(resource_path('./parameters.txt')) as file:
        parameters = [line.rstrip('\n') for line in file]
    # Prepare data and extract kms
    df = pd.read_excel(parameters[0])
    df.fillna('', inplace=True)
    df = df.astype({'Datum': 'str','von Str.': 'str','von Ort': 'str','von PLZ': 'str',
                'nach Str.': 'str','nach Ort': 'str','nach PLZ': 'str'})
    df["von PLZ"] = df["von PLZ"].apply(lambda x:x.split('.',1)[0])
    df["nach PLZ"] = df["nach PLZ"].apply(lambda x:x.split('.',1)[0])
    df["Kilometer"] = df.apply(lambda x:estimate_kilometers(x,parameters[1]),axis=1)
    # Calculate SUMs
    df = calculate_daily_sum(df)
    df_sum = pd.DataFrame.from_dict({'Datum':'SUMME','Kilometer':[df['Kilometer'].sum(axis=0)],'Kilometer ges./Tag':[df['Kilometer'].sum(axis=0)]})
    df = df.append(df_sum,ignore_index=True)
    # Save to Excel
    df.to_excel(parameters[0],index=False)