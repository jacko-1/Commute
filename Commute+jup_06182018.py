
# coding: utf-8

# In[2]:

# JBRJ
# 08.01.2017
# Import, clean, test, visualize commute

# Steps:
     # Import packages, raw data
     # Cleaning
     # For each set of groups we want to test:
    #     Map/create dummies
    #     Break into seperate DFs as per above
    #     Run T-test
    #     Store results in a pd.Series
    # Combine all Results into one summary table

# Import packages
import pandas as pd
import scipy.stats as stats

# Get data
df = pd.read_excel('Commute_data.xlsx',
 sheetname = 'Sheet1')





# In[ ]:




# In[4]:

# Clean time fields, create usable hr and minute versions
df['start_hr'] = df['start'].astype(str).str[:-2].astype(int)
df['start_min'] = df['start'].astype(str).str[-2:].astype(int)
df['end_hr'] = df['end'].astype(str).str[:-2].astype(int)
df['end_min'] = df['end'].astype(str).str[-2:].astype(int)

# Create time of commute variable (in minutes)
df['time'] = (df['end_hr'] - df['start_hr']) * 60  +  (df['end_min'] - df['start_min'])

# Simplify trains m -> r and 4 -> 5, these are interchangable
df['trains'] = df['trains'].str.replace("m", "r")
df['trains'] = df['trains'].str.replace("4", "5")
df['trains'] = df['trains'].str.replace("g", "6")
df['trains'].value_counts()


# In[5]:

## attempt to clean stupid routes:
df['drop_flag'] = df.groupby('trains')['trains'].transform('count')
df = df[df['drop_flag']>10]

train_type_dict = {"r":1,"rf6":2,"re":3,"bike":4,"rf5":5, "re65":6, "r5":7}
df['train_num'] = df['trains'].map(train_type_dict)


# In[6]:

df.head()
df['trains'].value_counts()


# In[27]:

#---------------------------------------------------------------
# ttest for Early vs Late
#---------------------------------------------------------------

def early_decider(hr_inp):
    if hr_inp < 8:
        return 1
    else:
        return 0

df['early_dy'] = df['start_hr'].map(early_decider)

df_early = df[df['early_dy'] == 1]
df_late = df[df['early_dy'] == 0]

results = stats.ttest_ind(df_early['time'], df_late['time'], nan_policy='omit')
p = results[1]
early_vs_late = pd.Series({'g1': 'early',
                        'g2': 'late',
                        'g1_mean':(df_early['time'].mean()),
                        'g2_mean':(df_late['time'].mean()),
                        'p_value': '{:05.4f}'.format(p)})


#---------------------------------------------------------------
# ttest for R vs. Express
#---------------------------------------------------------------

# define function to map R as a dummy
def exp_decider(exp_inp):
    if exp_inp == 'r':
        return 1
    else:
        return 0
df['r_dy'] = df['trains'].map(exp_decider)

df_r = df[df['r_dy'] == 1]
df_exp = df[df['r_dy'] == 0]

results = stats.ttest_ind(df_r['time'], df_exp['time'], nan_policy='omit')
p = results[1]
r_vs_exp = pd.Series({'g1': 'local',
                        'g2': 'express',
                        'g1_mean':(df_r['time'].mean()),
                        'g2_mean':(df_exp['time'].mean()),
                        'p_value': '{:05.4f}'.format(p)})


#---------------------------------------------------------------
# Ttest for re vs rf6 (E vs F)
#---------------------------------------------------------------

# Use f vs e
df_e = df[df['trains']=='re']
df_f = df[df['trains']=='rf6']
df_re65 = df[df['trains']=='re65']
df_rf5 = df[df['trains']=='rf5']
df_bike = df[df['trains']=='bike']
df_r5 = df[df['trains']=='r5']


results = stats.ttest_ind(df['time'].where(df['trains']=='re'), df['time'].where(df['trains']=='rf6'), nan_policy='omit')
#results = stats.ttest_ind(df_e['time'], df_f['time'], nan_policy='omit') ## Old versions
p = results[1]
e_vs_f = pd.Series({'g1': 'E',
                        'g2': 'F',
                        'g1_mean':(df_e['time'].mean()),
                        'g2_mean':(df_f['time'].mean()),
                        'p_value': '{:05.4f}'.format(p)})


#---------------------------------------------------------------
# Ttest for RF5 vs RF6
#---------------------------------------------------------------
results2 = stats.ttest_ind(df['time'].where(df['trains']=='rf6'), df['time'].where(df['trains']=='rf5'), nan_policy='omit')
p = results2[1]
rf6_vs_rf5 = pd.Series({'g1': 'RF6',
                        'g2': 'RF5',
                        'g1_mean':(df['time'].where(df['trains']=='rf6').mean()),
                        'g2_mean':(df['time'].where(df['trains']=='rf5').mean()),
                        'p_value': '{:05.4f}'.format(p)})

#---------------------------------------------------------------
# Ttest for RF5 vs R5 (ie is it worth it to add this train?, yes it is.)
#---------------------------------------------------------------
results3 = stats.ttest_ind(df['time'].where(df['trains']=='r5'), df['time'].where(df['trains']=='rf5'), nan_policy='omit')
p = results3[1]
rf5_vs_r5 = pd.Series({'g1': 'R5',
                        'g2': 'RF5',
                        'g1_mean':(df['time'].where(df['trains']=='r5').mean()),
                        'g2_mean':(df['time'].where(df['trains']=='rf5').mean()),
                        'p_value': '{:05.4f}'.format(p)})

#---------------------------------------------------------------
# Ttest for RF5 vs RFQ (RFQ is an easier xfer, are the stairs worth it?, no they are not)
#---------------------------------------------------------------
results4 = stats.ttest_ind(df['time'].where(df['trains']=='rfq'), df['time'].where(df['trains']=='rf5'), nan_policy='omit')
p = results4[1]
rf5_vs_rfq = pd.Series({'g1': 'RFQ',
                        'g2': 'RF5',
                        'g1_mean':(df['time'].where(df['trains']=='rfq').mean()),
                        'g2_mean':(df['time'].where(df['trains']=='rf5').mean()),
                        'p_value': '{:05.4f}'.format(p)})

#---------------------------------------------------------------
# Combine ttest results into a DF (results summary)
#---------------------------------------------------------------

test_results_df = pd.concat([early_vs_late, e_vs_f, r_vs_exp, rf6_vs_rf5, rf5_vs_r5, rf5_vs_rfq], axis=1).transpose()

# Create a fucntion to map p values into easier to read buckets
def p_simplifier(decim_inp):
    p_float = float(decim_inp)
    if p_float >=0.05:
        return 'not sig'
    elif p_float  <0.0001:
        return 'p < 0.0001'
    elif p_float <0.001:
        return 'p < 0.001'
    elif p_float  <0.01:
        return 'p < 0.01'
    elif p_float <0.05:
        return 'p < 0.05'
    else:
        return 'error'

test_results_df['p_summary'] = test_results_df['p_value'].map(p_simplifier)
test_results_df = test_results_df.rename(columns={'g1': 'Group 1', 'g2': 'Group 2', 'g1_mean': 'G1 Mean', 'g2_mean': 'G2 Mean'})
test_results_df


# In[28]:

## Summary stats df, loop through all values of train, and get descriptives of them
sum_frame = pd.DataFrame([])
for i in df['trains'].unique():
    key = pd.Series({   'train': i.upper(),
                        'mean':(df.where(df['trains']==i)['time'].mean()),
                        'med':(df.where(df['trains']==i)['time'].median()),
                        'min':(df.where(df['trains']==i)['time'].min()),
                        'max':(df.where(df['trains']==i)['time'].max()),
                        'std':(df.where(df['trains']==i)['time'].std())})
    sum_frame = sum_frame.append(key, ignore_index=True)
    
## Reorder columns in summary table
sum_frame = sum_frame[['train', 'min', 'max', 'med', 'mean', 'std']]  


# In[35]:

df['t_freq'] = df.groupby(['time', 'trains'])['time'].transform('count')
df.head(20)


# In[20]:




# In[47]:



#---------------------------------------------------------------
# Cleaning
#---------------------------------------------------------------

# For now, do not analyze bike/odd train choices, drop rows with notes
#df = df[df['notes'].isnull()]



#---------------------------------------------------------------
# visualization (scatter)
#---------------------------------------------------------------
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


## Add a column that is a freq of times, for plotting putposes:
# An annoying warning is issued, and summarily ignored by me
df_r = df.where(df['trains']=='r')
df_e = df.where(df['trains']=='re').where(df['time']<90)
df_f = df.where(df['trains']=='rf6')
df_bike = df.where(df['trains']=='bike')
df_re65 = df.where(df['trains']=='re65').where(df['time']<90)
df_rf5 = df.where(df['trains']=='rf5')

#df_r['t_freq'] = df_r.groupby('time')['time'].transform('count')
#df_e['t_freq'] = df_e.groupby('time')['time'].transform('count')
#df_f['t_freq'] = df_f.groupby('time')['time'].transform('count')
#df_bike['t_freq'] = df_bike.groupby('time')['time'].transform('count')

#{"r":1,"rf6":2,"re":3,"bike":4,"rf5":5, "re65":6, "r5":7}

## Plot 5 verticle lines for trains, sizes of dots based on frequency of time
plt.scatter(df_r['train_num'], df_r['time'], s=df_r['t_freq']**3, c='darkgoldenrod')
plt.scatter(df_f['train_num'], df_f['time'], s=df_f['t_freq']**3, c='darkorange')
plt.scatter(df_e['train_num'], df_e['time'], s=df_e['t_freq']**3, c='blue')
plt.scatter(df_bike['train_num'], df_bike['time'], s=df_bike['t_freq']**3, c='red')

### activate this code  for n = 5 trains types type chart (not update)
plt.scatter(df_re65['train_num'], df_re65['time'], s=df_re65['t_freq']**3, c=('blue', 'green'))
plt.scatter(df_rf5['train_num'], df_rf5['time'], s=df_rf5['t_freq']**3, c=('orange', 'green'))
plt.xticks(range(1,7, 1),['R','F','E', 'Bike', 'rf5', 're65'])

## Format and label chart
#plt.xticks(range(1,5, 1),['R','F','E', 'Bike'])
plt.xlabel('Train(s) Utilized')
plt.ylabel('Minutes')
plt.title('Jack\'s Commute Time to Work')
plt.tick_params(
    axis = 'both',          # changes apply to the x-axis
    which = 'both',      # both major and minor ticks are affected
    bottom = 'off',
    left = 'off',      # ticks along the bottom edge are off
    labelbottom = 'on',
    labelleft = 'on')
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
plt.savefig('scatter_06182018.png',dpi = 200)
## Display outputs
plt.show()
test_results_df
sum_frame

## Save outputs

writer = pd.ExcelWriter('Commute_output_06182018.xlsx')
test_results_df.to_excel(writer, sheet_name = 'ttests')
sum_frame.to_excel(writer, sheet_name = 'summary')
writer.save()




# In[45]:




# In[ ]:



