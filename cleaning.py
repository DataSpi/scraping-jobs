
import pandas as pd
import numpy as np
from pandasql import sqldf
import os 
import re
# os.chdir('/Users/spinokiem/Documents/1. Data_Science/1. Learning Folder/scraping-joblisting-sites/CareerBuilder')
import datetime as dt

################################################
# loading the dataset in from csv
df = pd.read_csv('data/raw/xnk/04102023-xuat-nhap-khau.csv')
today = dt.date(2023, 10, 4)
df.columns

# remove unnecessary columns
rm_cols = ['Phương thức làm việc']
df.drop(rm_cols, axis='columns', inplace=True)

# # rename cols
# df.columns = ['job_link', 'job_title', 'comp_name', 'salary', 'location',
#        'welfare', 'expire_date', 'update_date', 'industry', 'staff_type',
#        'exp', 'job_level', 'benefits', 'job_desc', 'job_require',
#        'other_infos', 'job_tags'] # KeyError: "['welfare', 'job_require', 'other_infos'] not in index"

################################################
# removing redundant character
df.job_title = df.job_title.str.replace('(Mới)', '').str.strip().str.lower()
df.location = df.location.str.replace('\n', ',')
# df.benefits = df.benefits.str.replace('\\n', ',')
# df.job_tags = df.job_tags.str.replace('\\n', ',')
df.exp = df.exp.str.replace('\\n', '').str.strip().str.lower()
df.expire_date = df.expire_date.str.replace("Hạn nộp: ", '')
# this is for the case the dataframe is loaded from csv file, then each elements of update_date would be a string
    # if the dataframe loaded directly from the scraper code, then each elements of update_date would be a list of 1 string
df.update_date = df.update_date.str.replace("['", '').str.replace("']", '')

## other_infos
# df.other_infos = df.other_infos.str.replace('\\n', ',').str.replace('\\t', '')
# df.other_infos = df.other_infos.apply(lambda x: re.sub(',+', '', x))

## let's just forget about job_desc for now
# df.job_require = df.job_require.str.replace('\\xa0', '').str.replace('\\n', '\n')


################################################
# working with date values: expire_date & update_date
## update_date
df.update_date = df['update_date'].apply(lambda x: pd.to_datetime(x, dayfirst=True))

## expire_date
df.expire_date = df.expire_date.fillna('just any string') # have to fillna() to make the following code works
df.loc[df.query('expire_date.str.contains("Hôm nay")').index, 
       'expire_date'] = today

mani_index = df[df.expire_date.str.contains('chỉ còn', na=False)].index 
# df.loc[mani_index]
    # list of index being manipulated. I don't know why I have to add na=False here, 
    # because it seems to me there is not NA after applying contains(). but anyway, this works & I don't have much time
df.loc[mani_index, 'expire_date']\
    = df.loc[mani_index, 'expire_date']\
            .apply(lambda x: re.findall(r'\d+', x))\
            .map(lambda x: int(x[0]))\
            .apply(lambda x: today + dt.timedelta(x))
            # (1) find number in elements containing 'chỉ còn' 
            # -> (2) turn them to int 
            # -> (3) turn them to datetime & add today to them.              
df.expire_date = df['expire_date'].apply(lambda x: pd.to_datetime(x, dayfirst=True, errors='coerce'))
    # values that can not be converted will be turned into NaT. 
    # values at mani_index will remained unchanged, because they are already in datetime.date dtype

################################################
# working with salary, create sal_min, sal_max
df.salary=df.salary.str.replace(",000,000", ' Tr').str.replace(',000', '000')
df[['sal_min', 'sal_max']] = df.salary.str.replace(",", ".").str.split('-', expand=True)
df['currency']=df.salary.str.split(" ").str[-1]
df.currency=df.currency.replace('tranh', None).replace('failed', None)#.value_counts()
df.sal_min = df.sal_min.str.extract(r'(\d+\.?\d*)', expand=False).replace('', np.nan).astype(float)
df.sal_max = df.sal_max.str.extract(r'(\d+\.?\d*)', expand=False).replace('', np.nan).astype(float)

# If salary contains 'Trên' -> sal_min, if salary contains 'Lên đến' -> sal_max
for i in df.query('sal_min.notna() & sal_max.isna()').index:#[['salary', 'sal_min', 'sal_max']]
    if 'Trên' in df.salary[i]:
        df.loc[i, 'sal_min'] = df.loc[i, 'sal_min']
    elif 'Lên đến' in df.salary[i]:
        df.loc[i, 'sal_max'] = df.loc[i, 'sal_min']
        df.loc[i, 'sal_min'] = np.nan
df[['sal_min', 'sal_max', 'currency']]
        
# working with exp, creating exp_min, exp_max
df[['exp_min', 'exp_max']] = df.exp.str.split('-', expand=True)
df['exp_measurement']=df.exp.str.split(" ").str[-1]
df.exp_measurement=df.exp_measurement.replace('failed', None)#.value_counts()
df.exp_min = df.exp_min.str.extract(r'(\d+\.?\d*)', expand=False).replace('', np.nan).astype(float)
df.exp_max = df.exp_max.str.extract(r'(\d+\.?\d*)', expand=False).replace('', np.nan).astype(float)
df.loc[df.exp == 'Chưa có kinh nghiệm', ['exp_min', 'exp_max']] = 0

# If exp contains 'Trên' -> exp_min, if exp contains 'Lên đến' -> exp_max
for i in df.query('exp_min.notna() & exp_max.isna()').index:
    if 'Trên' in df.exp[i]:
        df.loc[i, 'exp_min'] = df.loc[i, 'exp_min']
    elif 'Lên đến' in df.exp[i]:
        df.loc[i, 'exp_max'] = df.loc[i, 'exp_min']
        df.loc[i, 'exp_min'] = np.nan
# df[['exp_min', 'exp_max', 'exp_measurement']]


################################################
# working with multi_tag_col: ['location', 'welfare', 'job_tags', 'industry', 'benefits']

## create a function for getting dummies form multi_tag_col
def create_dummies_multi_tag(dataframe, column_name, sep):
    # Split the 'column' by `sep` and create a list of unique value in that column
    unique_list = dataframe[column_name].str.split(sep, expand=True).stack().str.strip().unique()
    # create dummies for each unique_value
    for i in unique_list: 
        dataframe[f'{column_name}_{i}'] = dataframe[column_name].str.contains(i).fillna(False).astype(int)

## creating dummies
multi_tag_cols = ['location', 'industry']
for col in multi_tag_cols:
    create_dummies_multi_tag(dataframe=df, column_name=col, sep=',')
# df.columns

# for i in df.salary:
#     print(i)

################################################
# saving the result to a cleaned dataset. 

df_cleaned = df.drop(['industry', 'exp', ], axis='columns')#'benefits', 'job_desc', 'job_tags'
## creating job_id
df_cleaned['job_id'] = df_cleaned.job_link.str.split('.').apply(lambda x: x[-2])
# df_cleaned.drop(labels='job_link', axis='columns', inplace=True)
df_cleaned.head()
# saving
df_cleaned.to_csv('data/processed/xnk/04102023-xuat-nhap-khau.csv', index=False)
