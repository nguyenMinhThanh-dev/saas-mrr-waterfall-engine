import pandas as pd
import numpy as np
subscription_events = pd.read_csv(r"C:\Users\mthan\saas-mrr-waterfall-engine\dataset\subscription_events.csv")
fx_rates = pd.read_csv(r"C:\Users\mthan\saas-mrr-waterfall-engine\dataset\fx_rates.csv")
print('Explorate Data')
print('supscription_events information:')
print(subscription_events.head())
print(subscription_events.info())
print('fx_rates information:')
print(fx_rates.head())
print(fx_rates.info())
print('======================================')

print('Requirement 1: Data Hygiene & Point-in-Time FX Conversion \n')
print("1a. Impute missing currency values based on each customer`s most frequent known currency (defaulting to 'USD' if unknown): ")
subscription_events_cleaned = subscription_events.copy()
print('Total NaN currency before filling:',subscription_events_cleaned['currency'].isna().sum())
subscription_events_cleaned['currency'] = subscription_events_cleaned['currency'].fillna('USD')#Fill all NaN currency into USD
print('Total NaN currency after filling:',subscription_events_cleaned['currency'].isna().sum())
print('--------------------------------------')

print("1b. Standarlize all plan_mrr amounts into USD using point-in-time daily exchange rates (fx_rates):")
subscription_events_cleaned['event_time'] = pd.to_datetime(subscription_events_cleaned['event_time']) 
fx_rates['rate_date'] = pd.to_datetime(fx_rates['rate_date'])
subscription_events_cleaned['event_date'] = subscription_events_cleaned['event_time'].dt.floor('D') #Create temporary column to merge
subscription_events_cleaned = pd.merge(subscription_events_cleaned, fx_rates, left_on= ['event_date', 'currency'], right_on = ['rate_date', 'currency'], how = 'left')
subscription_events_cleaned = subscription_events_cleaned.drop('event_date', axis = 1)
subscription_events_cleaned['standarlized_plan_mrr'] = (subscription_events_cleaned['plan_mrr'] * subscription_events_cleaned['rate_to_usd']).round(2) #calculate the standard plan mrr
print(subscription_events_cleaned.head(20))
print('======================================')


print("Requirement 2: Sequence Reconstruction & Monthly State Snapshot")
print("2a. Re-order asynchronous, out-of-order event logs chronologically across distributed servers:")
subscription_events_cleaned = subscription_events_cleaned.sort_values(['customer_id', 'event_time']).reset_index(drop = True)
print(subscription_events_cleaned.head(20))
print('--------------------------------------')

print("2b. Reconstruct the true end-of-month MRR state for every customer across all 12 calendar months (2025-01 to 2025-12):")
subscription_events_cleaned['year_month'] = subscription_events_cleaned['event_time'].dt.to_period('M').astype(str)
monthly_last_event = subscription_events_cleaned.groupby(['customer_id', 'year_month']).last().reset_index()
all_customers = subscription_events_cleaned['customer_id'].unique()
all_months = [f'2025-{m:02}' for m in range(1, 13)]
full_grip = pd.MultiIndex.from_product([all_customers, all_months], names = ['customer_id', 'year_month']).to_frame().reset_index(drop = True)
monthly_snapshot = pd.merge(full_grip, monthly_last_event, on = ['customer_id', 'year_month'], how = 'left')
print(monthly_snapshot.head(20))
print('--------------------------------------')

print("2c. Carry forward active MRR states for inactive months and default pre-signup states to $0: ")
monthly_snapshot['standarlized_plan_mrr'] = monthly_snapshot.groupby('customer_id')['standarlized_plan_mrr'].ffill().fillna(0)
print(monthly_snapshot.head(20))
print('======================================')

print("Requirement 3: Categorized MRR Waterfall Engine")
print("Categorize month-over-month revenue movements strictly into 5 financial classifications")
monthly_snapshot['prev_month'] = monthly_snapshot.groupby('customer_id')['standarlized_plan_mrr'].shift(1).fillna(0) #Get the previous mrr
monthly_snapshot['cumulative_max_mrr'] = monthly_snapshot.groupby('customer_id')['prev_month'].cummax() #Track historical maximum mrr of all previous month
curr = monthly_snapshot['standarlized_plan_mrr']
prev = monthly_snapshot['prev_month']
prev_max = monthly_snapshot['cumulative_max_mrr']
#Define 5 conditions in 1 array
conditions = [
    (prev == 0) & (curr > 0) & (prev_max == 0), #New MRR
    (prev == 0) & (curr > 0) & (prev_max > 0), #Reactivation MRR
    (prev > 0) & (curr > prev), #Expansion MRR
    (prev > 0) & (curr < prev) & (curr > 0), #Contraction MRR
    (prev > 0) & (curr == 0), #Churn MRR
]
categories = ['New', 'Reactivation', 'Expansion', 'Contraction', 'Churn']
monthly_snapshot['categories_mrr'] = np.select(conditions, categories, default = 'Retained')
monthly_snapshot['delta_mrr'] = curr - prev
print(monthly_snapshot.head(30))
print('======================================')

print("Requirement 4: Net Revenue Retention (NRR) Matrix")
first_active = monthly_snapshot[monthly_snapshot['categories_mrr'] == 'New'][['customer_id', 'year_month']].rename(columns = {'year_month' : 'cohort_month'})
monthly_snapshot_cohort = pd.merge(monthly_snapshot, first_active, on = 'customer_id', how = 'inner')
ym_cohort = pd.to_datetime(monthly_snapshot_cohort['year_month'])
cohort_period = pd.to_datetime(monthly_snapshot_cohort['cohort_month'])
monthly_snapshot_cohort['relative_month'] = (ym_cohort.dt.year - cohort_period.dt.year) * 12 + (ym_cohort.dt.month - cohort_period.dt.month)
monthly_snapshot_cohort_6m = monthly_snapshot_cohort[(monthly_snapshot_cohort['relative_month'] >= 0) & (monthly_snapshot_cohort['relative_month'] <=5)]
#Aggregate total MRR by cohort and relative_month:
cohort_sumary = monthly_snapshot_cohort_6m.groupby(['cohort_month', 'relative_month'])['standarlized_plan_mrr'].sum().reset_index()
star_mrr = cohort_sumary[cohort_sumary['relative_month'] == 0][['cohort_month', 'standarlized_plan_mrr']].rename(columns = {'standarlized_plan_mrr' : 'initial_plan_mrr'})
cohort_sumary = pd.merge(cohort_sumary, star_mrr, on = 'cohort_month', how = 'inner')
cohort_sumary['nrr_percentage'] = ((cohort_sumary['standarlized_plan_mrr'] / cohort_sumary['initial_plan_mrr']) * 100).round(2)
print(cohort_sumary)
