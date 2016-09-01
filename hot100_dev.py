#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 21:36:49 2016

@author: dsaunder
"""
import os
import pandas as pd 
import re
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import wikipedia
import codecs
#%%
listdir = 'lists/'
hot100_files  = os.listdir(listdir)

data = pd.DataFrame()
for h_file in hot100_files:
    if '.txt' not in h_file:
        continue
    year = int(h_file.split('.')[0])
    if year == 2016:
        with codecs.open(listdir + h_file,'r',encoding='utf-8') as f:
            names = []
            mranks = []
            waiting_for_rank = False
            for line in f:
                result = re.match('(.*) Maxim Rank - (\d+)', line)
                if result:
                    name, mrank = result.groups()
                    names.append(name.strip())
                    mranks.append(int(mrank))
            df = pd.DataFrame({'name':names,'mrank':mranks})
    else:
        df = pd.read_csv(listdir+ h_file, header=None, names=['name'], encoding='utf-8')
        df.loc[:,'name'] = df.loc[:,'name'].apply(lambda x: x.strip())
        df.loc[:,'mrank'] = df.index+1
    df.loc[:,'year'] = year
    

    data = data.append(df, ignore_index=True)
#%%
data.to_csv('maxim_hot_100.csv',index=False, encoding='utf-8')
#%%
# Collect all the ages for women who have them listed in their 
# wikipedia pages (and for whom there are not more than 1 wikipedia hits)
import time
from dateutil.parser import parse
start = time.time()

gay_keywords = ['Lesbian','Bisexual','LGBT people','LGBT actresses']
trans_keywords = ['Transgender']
all_names = np.unique(data.name)
person_info = pd.DataFrame()
counter = 1
for name in all_names:
    if np.mod(counter,10) == 0:
        print "%d of %d " % (counter,len(all_names))
        print (time.time() - start)/ 60.
    counter = counter + 1
#    try: 
#        w_page_name = wikipedia.search(name, results=1)[0]
#    except IndexError:
#        print name + "\tNo wikipedia hits" 
#        continue 
    

    try:
        page = wikipedia.page(name,auto_suggest=False,redirect=False)
    except wikipedia.DisambiguationError:
        print name + "\tToo many wikipedia hits" 
        continue
    except wikipedia.PageError:
        print name + "\tNo wikipedia hits" 
        continue
    except wikipedia.RedirectError:
        print name + "\tRedirect error"
        continue

    page_source = page.html()
    results = re.search('<span class=\"bday\">([^<]*)</span>', page_source)
    if not results:
        print name+ "\tNo birthdate"
#        print page_source
        continue
    birthdate = results.groups()[0]
    print name + "\t" + birthdate
    person_info.loc[name,'birthdate' ] = birthdate

    alma_result = re.findall('Alma&#160;mater</th><td>\n(.*)</tr>', page_source,re.MULTILINE)    
    if alma_result:
        print name + "\tAlma mater\t" + alma_result[0]
        person_info.loc[name,'college_listed'] = 1
    else:
        person_info.loc[name,'college_listed'] = 0

    birthplace_result = re.search('<span class=\"birthplace\">(.*)</span>',page_source)
    if birthplace_result:
        print name + "\tBirthplace\t" + birthplace_result.groups()[0]
        
        if any(a in birthplace_result.groups()[0] for a in ['U.S.','United States','US','California','New York']):
            person_info.loc[name,'us_born'] = 1
        else:
            person_info.loc[name,'us_born'] = 0

    if any(any(keyword in category for keyword in gay_keywords) for category in page.categories):
        person_info.loc[name,'lesbian_or_bi'] = 1
    else:
        person_info.loc[name,'lesbian_or_bi'] = 0
        
    if any(any((keyword in category) and (not 'activist' in category) for keyword in trans_keywords) for category in page.categories):
        person_info.loc[name,'trans'] = 1
    else:
        person_info.loc[name,'trans'] = 0

print '%d out of %d with unambiguous birthdates (%.1f%%)' % (len(person_info), len(all_names), 100* float(len(person_info))/len(all_names))
#%%
person_info.to_csv('maxim_person_info.csv',index=True, encoding='utf-8')

#%%
# Parse the date and extract the year
for name,bd in person_info.iterrows():
    the_date = parse(bd.values[0]) # General purpose date string interpretation
    person_info.loc[name,'dt'] = the_date
    person_info.loc[name,'birth_year'] =the_date.year
#%%
with_ages = data.merge(person_info, how='right', left_on='name', right_index=True)
#%%
with_ages.loc[:,'age_at_time'] = with_ages.year - with_ages.birth_year
print with_ages.loc[with_ages.age_at_time==np.min(with_ages.age_at_time),:]
print with_ages.loc[with_ages.age_at_time==np.max(with_ages.age_at_time),:]
              
plt.figure()
sns.distplot(with_ages.age_at_time,bins=range(10,51))
#%%
print with_ages.loc[with_ages.birth_year==np.min(with_ages.birth_year),:]
print with_ages.loc[with_ages.birth_year==np.max(with_ages.birth_year),:]
#%%
by_name = data.groupby(by='name')
num_years = by_name['year'].count()
plt.figure()
sns.distplot(num_years, bins = range(1,18), kde=False)
plt.xticks(range(1,19))
#%%
# Look at the trajectories of women's Hot 100 "careers", by representing their
# first year as 1 and so forth, and their highest ranking as 1and their lowest
# as 0 

trajectories = pd.DataFrame()

for name in num_years[num_years > 5].index:
    entries = data[data.name == name]
    entries.sort_values('year')
#    plt.figure()
#    plt.plot(entries.year,entries.mrank,'.',markersize=25)
#    plt.title('%s (%d entries, mean rank %.1f)' % (name, len(entries), np.mean(entries.mrank)))
#    plt.ylim([1,100])
#    plt.xlim([2000,2016])
#    plt.xticks(range(2000,2017))
#    plt.gca().invert_yaxis()

    trajectory = pd.DataFrame({'mrank':entries.mrank.values}, index=(1+entries.year-np.min(entries.year)))
    trajectory = trajectory.reindex(range(np.min(trajectory.index.values), np.max(trajectory.index.values)+1),fill_value=101)
    normalized_trajectory = trajectory - np.min(trajectory)
    normalized_trajectory = 1- (normalized_trajectory / np.max(normalized_trajectory))
    to_add = pd.DataFrame({'mrank':trajectory.mrank, 'mrank_normalized':normalized_trajectory.mrank, 'year_of_run':trajectory.index})
    to_add.loc[:,'name'] = name
    to_add.loc[:,'year'] = trajectory.index+np.min(entries.year) - 1
    trajectories = trajectories.append(to_add)
    
    plt.figure()
    plt.plot(trajectory.index,normalized_trajectory,'.',markersize=25)
    plt.title('%s (%d entries, mean rank %.1f)' % (name, len(entries), np.mean(trajectory)))
    plt.ylim([0,1])
    plt.xlim([1,17])
    plt.xticks(range(1,17))
 
#%%

plt.figure()
for name in np.unique(trajectories.name):
    indices = trajectories.name == name
    plt.plot(trajectories.loc[indices,'year'], trajectories.loc[indices,'mrank'],'.-',markersize=15)
plt.gca().invert_yaxis()
plt.legend(np.unique(trajectories.name),loc='best')
#%%
plt.figure()
sns.pointplot(x='year_of_run', y='mrank', data=trajectories, estimator=np.mean)
plt.gca().invert_yaxis()
#%%
plt.figure()
sns.boxplot(x='year_of_run', y='mrank', data=trajectories)
plt.gca().invert_yaxis()
#%%
plt.figure()
sns.swarmplot(x='year_of_run', y='mrank', hue='name', data=trajectories)

#%%
# Was there a different distribution of ages in different years?
plt.figure()
sns.boxplot(x='year',y='age_at_time',data=with_ages)

#%%
# Was there a different distribution of ages in different years?
plt.figure()
sns.swarmplot(x='year',y='age_at_time',data=with_ages.loc[(with_ages.mrank<=10),:])
#%%
plt.figure()
sns.swarmplot(x='year',y='age_at_time',data=with_ages.loc[(with_ages.mrank<=50),:])

#%%
plt.figure()
sns.pointplot(x='year',y='age_at_time',data=with_ages, color=sns.xkcd_rgb["light red"])
#sns.violinplot(x='year',y='age_at_time',data=with_ages)
sns.pointplot(x='year',y='age_at_time',data=with_ages, color=sns.xkcd_rgb["light orange"],estimator=np.median)

#%%
# Proportion with an alma mater listed
plt.figure()
sns.pointplot(x='year',y='college_listed',data=with_ages, ci = 0, color=sns.xkcd_rgb["light purple"], estimator=np.nanmean)
#%%
# Proportion US born by year
plt.figure()
sns.pointplot(x='year',y='us_born',data=with_ages, ci = 0, color=sns.xkcd_rgb["light purple"], estimator=np.nanmean)
#%%
# Number lesbian or bi by year
plt.figure()
sns.pointplot(x='year',y='lesbian_or_bi',data=with_ages, ci = 0, color=sns.xkcd_rgb["light purple"], estimator=np.nansum)
#%%
# Number trans by year
plt.figure()
sns.pointplot(x='year',y='trans',data=with_ages, ci = 0, color=sns.xkcd_rgb["light purple"], estimator=np.nansum)
#%%
# Average rank of us vs non us born by year 
plt.figure()
sns.pointplot(x='year',y='mrank',data=with_ages, hue='us_born', ci=0, estimator=np.nanmean)
plt.gca().invert_yaxis()
#%%
# Top 10 for the year number US born
plt.figure()
sns.pointplot(x='year',y='us_born',data=with_ages.loc[(with_ages.mrank<=10) ,:], ci=0, estimator=np.nansum)
#%%
# Top 10 number college listed
plt.figure()
sns.pointplot(x='year',y='college_listed',data=with_ages.loc[(with_ages.mrank<=10) ,:], ci=0, estimator=np.nansum)
plt.ylim([-0.05,10])