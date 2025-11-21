import pandas as pd
import matplotlib.pyplot as plt
import locale
import os
import numpy as np

# ----------------------------
# Türkçe yerel ayar (para birimi için)
# ----------------------------
try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Turkish_Turkey.1254')
    except locale.Error:
        print("Warning: Turkish locale not set. Currency formatting may be default.")

# ----------------------------
# Style
# ----------------------------
plt.rcParams['figure.facecolor'] = '#ffffff'  # White background
plt.rcParams['axes.facecolor'] = '#ffffff'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['legend.fontsize'] = 10

# ----------------------------
# File paths
# ----------------------------
INPUT_FILE = 'inventory.csv'
OUTPUT_DIR = 'output_day2'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------
# Read data
# ----------------------------
df = pd.read_csv(INPUT_FILE)

# Total cost per SKU
sku_cost = df.groupby('Material_ID')['Total_Cost'].sum().reset_index()
sku_cost = sku_cost.sort_values(by='Total_Cost', ascending=False)
sku_cost['Cumulative_Cost'] = sku_cost['Total_Cost'].cumsum()
total_cost = sku_cost['Total_Cost'].sum()

# Pareto principle: top 20% SKUs ~ 80% of cost
sku_cost['Cumulative_Percent'] = sku_cost['Cumulative_Cost'] / total_cost * 100
sku_count = sku_cost.shape[0]
sku_cost['SKU_Percent'] = np.arange(1, sku_count + 1) / sku_count * 100

pareto_sku_count = int(sku_count * 0.20)
pareto_cost_percent = sku_cost.iloc[pareto_sku_count - 1]['Cumulative_Percent'] if pareto_sku_count > 0 else 0
cutoff_sku_count = sku_cost[sku_cost['Cumulative_Percent'] <= 80].shape[0]
cutoff_sku_percent = (cutoff_sku_count / sku_count) * 100

print(f"Total SKU count: {sku_count}")
print(f"\n🎯 PARETO PRINCIPLE:")
print(f"   • Top 20% SKUs ({pareto_sku_count}) contribute {pareto_cost_percent:.1f}% of total cost")
print(f"   • Number of SKUs contributing 80% of cost: {cutoff_sku_count} ({cutoff_sku_percent:.1f}%)")

# Save ABC data
sku_cost.to_csv(os.path.join(OUTPUT_DIR, 'abc_analysis.csv'), index=False)

# ----------------------------
# Plot 1: ABC Pareto Chart
# ----------------------------
fig, ax1 = plt.subplots(figsize=(14, 7))

bars = ax1.bar(range(sku_count), sku_cost['Total_Cost'], 
               color='#3498db', alpha=0.8, label='SKU Cost', edgecolor='#2980b9', linewidth=0.5)
ax1.set_xlabel('SKUs sorted by Total Cost', fontweight='bold')
ax1.set_ylabel('Total Cost (₺)', color='#3498db', fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#3498db')

ax2 = ax1.twinx()
line = ax2.plot(range(sku_count), sku_cost['Cumulative_Percent'], 
                color='#808080', linewidth=3, marker='o', markersize=3, 
                label='Cumulative %', markevery=max(1, sku_count//20))
ax2.set_ylabel('Cumulative %', color='#808080', fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#808080')
ax2.set_ylim(0, 105)

# Reference lines
ax2.axhline(y=80, color='#e74c3c', linestyle='--', linewidth=2.5, alpha=0.8, label='80% Cost Threshold')
ax1.axvline(x=pareto_sku_count, color='#27ae60', linestyle='--', linewidth=2.5, alpha=0.8, label=f'20% SKUs ({pareto_sku_count})')
ax2.fill_between(range(pareto_sku_count + 1), 0, 105, alpha=0.1, color='#27ae60')

ax1.set_title('ABC Analysis – Pareto Diagram (20% SKUs ≈ 80% Cost)', fontsize=14, fontweight='bold', pad=20)
ax1.grid(True, alpha=0.3, axis='y')
ax1.set_axisbelow(True)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', framealpha=0.95)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'abc_analysis_pareto.png'), dpi=300, bbox_inches='tight')
plt.show()

# ----------------------------
# Plot 2: ABC Category Pie Charts
# ----------------------------
a_items = sku_cost[sku_cost['Cumulative_Percent'] <= 80]
b_items = sku_cost[(sku_cost['Cumulative_Percent'] > 80) & (sku_cost['Cumulative_Percent'] <= 95)]
c_items = sku_cost[sku_cost['Cumulative_Percent'] > 95]

categories = ['Category A\n(High Value)', 'Category B\n(Medium Value)', 'Category C\n(Low Value)']
values = [a_items['Total_Cost'].sum(), b_items['Total_Cost'].sum(), c_items['Total_Cost'].sum()]
counts = [len(a_items), len(b_items), len(c_items)]
colors = ['#e74c3c', '#f39c12', '#3498db']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

wedges1, texts1, autotexts1 = ax1.pie(values, labels=categories, autopct='%1.1f%%',
                                      colors=colors, startangle=90, textprops={'fontsize': 11, 'weight': 'bold'},
                                      explode=(0.05, 0.05, 0.05))
ax1.set_title('Cost Distribution', fontsize=13, fontweight='bold', pad=20)

wedges2, texts2, autotexts2 = ax2.pie(counts, labels=categories, autopct='%1.1f%%',
                                      colors=colors, startangle=90, textprops={'fontsize': 11, 'weight': 'bold'},
                                      explode=(0.05, 0.05, 0.05))
ax2.set_title('SKU Count Distribution', fontsize=13, fontweight='bold', pad=20)

plt.suptitle('ABC Category Analysis', fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'abc_analysis_categories.png'), dpi=300, bbox_inches='tight')
plt.show()

# ----------------------------
# Plot: ABC Dashboard (Single Figure)
# ----------------------------
fig = plt.figure(figsize=(18, 10))
grid = fig.add_gridspec(2, 2, width_ratios=[2.2, 1], height_ratios=[1, 1], wspace=0.3, hspace=0.25)

# === PANEL 1: Pareto Chart (Large Left Panel) ===
ax1 = fig.add_subplot(grid[:, 0])   # spans 2 rows

ax1.bar(range(sku_count), sku_cost['Total_Cost'],
        color='#3498db', alpha=0.8, edgecolor='#2980b9', linewidth=0.5)
ax1.set_xlabel('SKUs sorted by Total Cost', fontweight='bold')
ax1.set_ylabel('Total Cost (₺)', color='#3498db', fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#3498db')
ax1.grid(True, alpha=0.3, axis='y')

ax2 = ax1.twinx()
ax2.plot(range(sku_count), sku_cost['Cumulative_Percent'],
         color='#2c3e50', linewidth=3)
ax2.set_ylabel('Cumulative %', color='#2c3e50', fontweight='bold')
ax2.set_ylim(0, 105)

ax2.axhline(80, color='#e74c3c', linestyle='--', linewidth=2)
ax1.axvline(pareto_sku_count, color='#27ae60', linestyle='--', linewidth=2)

ax1.set_title('ABC Analysis – Pareto Distribution', fontsize=15, fontweight='bold', pad=15)

# === PANEL 2: Cost Distribution Pie ===
ax3 = fig.add_subplot(grid[0, 1])

ax3.pie(values, labels=categories, autopct='%1.1f%%',
        colors=['#e74c3c', '#f39c12', '#3498db'],
        explode=(0.06, 0.06, 0.06), startangle=90,
        textprops={'fontsize': 11, 'fontweight': 'bold'})

ax3.set_title('Cost Distribution by ABC Category', fontsize=13, fontweight='bold')

# === PANEL 3: SKU Count Pie ===
ax4 = fig.add_subplot(grid[1, 1])

ax4.pie(counts, labels=categories, autopct='%1.1f%%',
        colors=['#e74c3c', '#f39c12', '#3498db'],
        explode=(0.06, 0.06, 0.06), startangle=90,
        textprops={'fontsize': 11, 'fontweight': 'bold'})

ax4.set_title('SKU Count Distribution', fontsize=13, fontweight='bold')

# === SAVE & SHOW ===
plt.suptitle("ABC Inventory Dashboard", fontsize=18, fontweight='bold', y=0.98)
plt.savefig(os.path.join(OUTPUT_DIR, 'abc_dashboard.png'),
            dpi=300, bbox_inches='tight')
plt.show()

print("📊 Dashboard exported: abc_dashboard.png")
