import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONSTANT COST AND EFFICIENCY PARAMETERS ---
# Gross monthly labor cost (Rounded estimate)
GROSS_MONTHLY_LABOR_COST = 1000 
# Gross annual labor cost (For one employee)
GROSS_ANNUAL_LABOR_COST = GROSS_MONTHLY_LABOR_COST * 12 # $12,000

# Extra Handling Efficiency Assumptions
AVG_ANNUAL_PICKS_PER_A_ITEM_IN_SLOW_ZONE = 20 # Annual picks per A-item in the slow zone
EXTRA_TIME_PER_PICK_SECONDS = 90 # Extra time required per pick from the slow zone (1.5 minutes)
WORK_DAYS_PER_YEAR = 250
WORK_HOURS_PER_DAY = 8
TOTAL_ANNUAL_WORK_SECONDS = WORK_DAYS_PER_YEAR * WORK_HOURS_PER_DAY * 3600 # 7,200,000 seconds

# Read your file
try:
    df = pd.read_csv('inventory.csv') 
except FileNotFoundError:
    print("inventory.csv file not found. Please check the path.")
    exit()

# --- 1. ABC Classification ---
df_abc = df.sort_values(by='Total_Cost', ascending=False).copy()
Total_Cost = df_abc['Total_Cost'].sum()
df_abc['Cum_Cost_Pct'] = (df_abc['Total_Cost'].cumsum() / Total_Cost) * 100

df_abc['ABC_Class'] = 'C'
df_abc.loc[df_abc['Cum_Cost_Pct'] <= 95, 'ABC_Class'] = 'B'
df_abc.loc[df_abc['Cum_Cost_Pct'] <= 80, 'ABC_Class'] = 'A'

# --- 2. Location Efficiency Analysis ---
if 'Location' in df_abc.columns:
    # Assumption for Fast Access locations (Customize this based on your warehouse codes)
    df_abc['Is_Fast_Access'] = df_abc['Location'].astype(str).str.contains('ZONEA', na=False, case=False) | \
                               df_abc['Location'].astype(str).str.contains('PZ', na=False, case=False) | \
                               df_abc['Location'].astype(str).str.contains('01$', na=False) 
else:
    print("Error: 'Location' column not found. Location efficiency analysis cannot be performed.")
    exit()

# A-Class items distribution
a_class_items = df_abc[df_abc['ABC_Class'] == 'A']
total_a_items = len(a_class_items)
a_in_slow_access = a_class_items[a_class_items['Is_Fast_Access'] == False]
a_in_slow_access_count = len(a_in_slow_access)

pct_a_in_fast_access = (len(a_class_items[a_class_items['Is_Fast_Access'] == True]) / total_a_items) * 100 if total_a_items > 0 else 0
pct_a_in_slow_access = 100 - pct_a_in_fast_access

# --- 3. Cost and Labor Analysis ---
total_extra_picks = a_in_slow_access_count * AVG_ANNUAL_PICKS_PER_A_ITEM_IN_SLOW_ZONE
total_extra_time_seconds = total_extra_picks * EXTRA_TIME_PER_PICK_SECONDS 

# Extra time percentage of a worker's total annual work time
extra_time_labor_pct = (total_extra_time_seconds / TOTAL_ANNUAL_WORK_SECONDS)

# Extra cost corresponding to the extra time
extra_labor_cost_usd = extra_time_labor_pct * GROSS_ANNUAL_LABOR_COST


# --- 4. Visualization (Dual Y-Axis for Cost/Time) ---

plt.figure(figsize=(14, 7)) # Increased figure size for better visibility
sns.set_style("whitegrid")
plt.suptitle('Warehouse Optimization Analysis: ABC and Hidden Labor Cost', fontsize=18, fontweight='bold', y=1.02)

# --- SUBPLOT 1: A-Class Item Location Distribution ---
plt.subplot(1, 2, 1) # 1 row, 2 columns, 1st plot
plot_data_loc = pd.DataFrame({
    'Access Type': ['Fast Access', 'Slow Access'],
    'Percentage': [pct_a_in_fast_access, pct_a_in_slow_access]
})

bars_loc = sns.barplot(x='Access Type', y='Percentage', data=plot_data_loc, palette=['#4CAF50', '#FF9800'])
plt.title('A-Class Items Location Efficiency', fontsize=15)
plt.ylabel('Percentage of A-Class Items (%)', fontsize=12)
plt.xlabel('Storage Zone', fontsize=12)
plt.ylim(0, 100)

for bar in bars_loc.patches:
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, 
             f'{bar.get_height():.2f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

# --- SUBPLOT 2: Dual Y-Axis for Extra Labor Load and Cost ---
ax1 = plt.subplot(1, 2, 2) # 1 row, 2 columns, 2nd plot

# Bar for Extra Labor Cost (using ax1 - primary axis)
# Using a dummy bar plot for the cost to show it clearly
cost_bar = ax1.bar(
    'Annual Extra Labor Cost', # X-position label
    extra_labor_cost_usd, 
    color='#2196F3', 
    width=0.4, # Adjust width to make space for the line plot marker
    label=f'Cost (${extra_labor_cost_usd:,.0f})'
)
ax1.set_ylabel('Extra Labor Cost (USD) / yearly', color='#2196F3', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#2196F3')
ax1.set_ylim(0, extra_labor_cost_usd * 1.3) # Set limit for cost axis

# Add the cost label on the bar
for rect in cost_bar:
    height = rect.get_height()
    ax1.text(rect.get_x() + rect.get_width()/2., height + (height*0.05),
            f'${height:,.2f}',
            ha='center', va='bottom', color='#0D47A1', fontweight='bold', fontsize=11)

# Secondary Y-axis for Extra Time Percentage (ax2)
ax2 = ax1.twinx() 

# Line/Marker for Extra Time Percentage (using ax2 - secondary axis)
time_pct = extra_time_labor_pct * 100
ax2.plot(
    'Annual Extra Labor Cost', # X-position, aligned with the bar
    time_pct, 
    color='#F44336', 
    marker='o', # Use a visible marker (circle)
    markersize=10, 
    linestyle='--', # Use a dashed line
    label=f'Time ({time_pct:.2f}%)'
)

ax2.set_ylabel('Extra Time (% of Annual Workload)', color='#F44336', fontsize=12) 
ax2.tick_params(axis='y', labelcolor='#F44336')
ax2.set_ylim(0, time_pct * 3) # Set limit for percentage axis

# Add the time percentage label
ax2.text(
    0, # X-position of the marker (which is 'Annual Extra Labor Cost')
    time_pct + (time_pct*0.1), 
    f'{time_pct:.2f}%', 
    ha='center', va='bottom', color='#B71C1C', fontweight='bold', fontsize=11
)

plt.title('Annual Extra Workload due to Slow Access', fontsize=15)
ax1.set_xlabel('Key Metric', fontsize=12)
ax1.grid(False) # Disable grid lines for ax1 to clean up the look

plt.tight_layout(rect=[0, 0, 1, 0.98]) 
plt.savefig('inventory_efficiency_and_cost_analysis_v2.png')
plt.show()

# --- 5. Professional English Console Output ---
print("\n" + "="*70)
print("📦 WAREHOUSE OPTIMIZATION & COST ANALYSIS SUMMARY")
print("="*70)
print(f"1. High-Value Items (A-Class) in SLOW Access Zone: {a_in_slow_access_count} units")
print(f"   (Percentage of A-Class Items in Slow Zone: {pct_a_in_slow_access:.2f}%)")
print("-" * 30)

print(f"2. Estimated Total Annual Extra Picks (Wasted Motion): {total_extra_picks:,.0f} picks")
print(f"3. Total Annual Extra Time Spent: {total_extra_time_seconds:,.0f} seconds")
print("-" * 30)

print(f"4. Extra Time as a Percentage of Annual Workload: {extra_time_labor_pct*100:.2f}%")
print(f"5. Estimated ANNUAL EXTRA LABOR COST due to Slow Zone: ${extra_labor_cost_usd:,.2f} USD")
print(f"   (Calculation based on Gross Annual Labor Cost: ${GROSS_ANNUAL_LABOR_COST:,.0f}/year)")
print("Dual-Axis Chart saved as 'inventory_efficiency_and_cost_analysis_v2.png'.")
print("="*70)