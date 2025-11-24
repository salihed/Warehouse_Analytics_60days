import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. SABİT PARAMETRELER VE SÜTUN EŞLEŞTİRMELERİ ---

# Finansal ve Operasyonel Varsayımlar
GROSS_MONTHLY_LABOR_COST = 1500 
GROSS_ANNUAL_LABOR_COST = GROSS_MONTHLY_LABOR_COST * 12 # $18,000 USD 
#                               ^^^^
# Hata buradaydı: GROS_MONTHLY_LABOR_COST yerine GROSS_MONTHLY_LABOR_COST olmalı.

EXTRA_TIME_PER_PICK_SECONDS = 120 # Sabit: 2 dakika = 120 saniye
WORK_DAYS_PER_YEAR = 250
WORK_HOURS_PER_DAY = 8
TOTAL_ANNUAL_WORK_SECONDS = WORK_DAYS_PER_YEAR * WORK_HOURS_PER_DAY * 3600

TOP_N_RELOCATION = 250 # <--- DEĞİŞİKLİK BURADA: Kapsam 250 ürüne çıkarıldı

# Sütun Eşleştirmeleri
PRODUCT_ID_COL_INV = 'Material_ID'
COST_COL = 'Total_Cost'
LOCATION_COL = 'Location'
PRODUCT_ID_COL_OUT = 'Material_ID'

# --- 2. VERİ YÜKLEME VE ÖN İŞLEME ---
try:
    df_inv = pd.read_csv('inventory.csv') 
    df_out = pd.read_csv('outbound_movements.csv') 
    
    df_inv.rename(columns={PRODUCT_ID_COL_INV: 'Product_ID'}, inplace=True)
    df_out.rename(columns={PRODUCT_ID_COL_OUT: 'Product_ID'}, inplace=True)
        
except FileNotFoundError:
    print("Hata: Gerekli CSV dosyalarından biri bulunamadı.")
    exit()

# --- 3. ABC SINIFLANDIRMASI VE LOKASYON ANALİZİ ---
df_abc = df_inv.sort_values(by=COST_COL, ascending=False).copy()
Total_Cost_Sum = df_abc[COST_COL].sum()
df_abc['Cum_Cost_Pct'] = (df_abc[COST_COL].cumsum() / Total_Cost_Sum) * 100
df_abc['ABC_Class'] = 'C'
df_abc.loc[df_abc['Cum_Cost_Pct'] <= 95, 'ABC_Class'] = 'B'
df_abc.loc[df_abc['Cum_Cost_Pct'] <= 80, 'ABC_Class'] = 'A'
df_abc['Is_Fast_Access'] = df_abc[LOCATION_COL].astype(str).str.contains('ZONEA', na=False, case=False) | \
                           df_abc[LOCATION_COL].astype(str).str.contains('PZ', na=False, case=False) | \
                           df_abc[LOCATION_COL].astype(str).str.contains('01$', na=False) 

# --- 4. DEVİR HIZI (PICK COUNT) HESAPLAMA VE BİRLEŞTİRME ---
df_picks = df_out.groupby('Product_ID').size().reset_index(name='Annual_Pick_Count')
df_final = pd.merge(df_abc, df_picks, on='Product_ID', how='left')
df_final['Annual_Pick_Count'] = df_final['Annual_Pick_Count'].fillna(0).astype(int)

# --- 5. MALİYET HESAPLAMALARI (TOP 250 ODAKLI) ---

# A. TÜM YAVAŞ BÖLGE A-ÜRÜNLERİNDEN KAYNAKLANAN TOPLAM FAZLA MALİYET (Referans Noktası)
df_all_slow_A = df_final[
    (df_final['ABC_Class'] == 'A') & 
    (df_final['Is_Fast_Access'] == False)
].copy()

total_extra_picks_ALL = df_all_slow_A['Annual_Pick_Count'].sum()
total_extra_time_seconds_ALL = total_extra_picks_ALL * EXTRA_TIME_PER_PICK_SECONDS 
excess_operational_cost_ALL = (total_extra_time_seconds_ALL / TOTAL_ANNUAL_WORK_SECONDS) * GROSS_ANNUAL_LABOR_COST

# B. TOP 250 EN HIZLI DEVİR HIZINA SAHİP ÜRÜNÜ TAŞIMANIN GETİRECEĞİ NET KAZANIM
df_slow_A_priority = df_all_slow_A.sort_values(by='Annual_Pick_Count', ascending=False)
df_top_relocate = df_slow_A_priority.head(TOP_N_RELOCATION)

total_extra_picks_top_250 = df_top_relocate['Annual_Pick_Count'].sum()
labor_cost_gain = (total_extra_picks_top_250 * EXTRA_TIME_PER_PICK_SECONDS / TOTAL_ANNUAL_WORK_SECONDS) * GROSS_ANNUAL_LABOR_COST

# Yüzdelik Kazanım
pct_gain = (labor_cost_gain / excess_operational_cost_ALL) * 100 if excess_operational_cost_ALL > 0 else 0

# --- 6. VİSUALİZASYON (TOP 250 NET KAZANIM VE OPERASYONEL ETKİ) ---
# (Y ekseni limiti dinamik olarak belirlenir)
y_max_limit = excess_operational_cost_ALL * 1.15

plt.figure(figsize=(16, 7)) 
sns.set_style("whitegrid")

# Subplot 1: Finansal Kazanım
ax1 = plt.subplot(1, 2, 1)

plot_data_cost_gain = pd.DataFrame({
    'Metric': ['Total Potential Gain', f'Actual Gain (Top {TOP_N_RELOCATION})'],
    'Cost_USD': [excess_operational_cost_ALL, labor_cost_gain],
    'Color': ['#34495E', '#2ECC71']
})

bars_cost = sns.barplot(
    x='Metric', y='Cost_USD', data=plot_data_cost_gain, 
    palette=plot_data_cost_gain['Color'].tolist(), ax=ax1
)

ax1.set_title(f'Financial Impact: Top {TOP_N_RELOCATION} vs. Max Potential (2 Min. Diff)', fontsize=15, fontweight='bold')
ax1.set_ylabel('Annual Net Gain (USD)', fontsize=12)
ax1.set_xlabel('')
ax1.tick_params(axis='x', rotation=0)
ax1.set_ylim(0, y_max_limit) 


# Veri Etiketleri
for i, bar in enumerate(bars_cost.patches):
    y_pos = bar.get_height() + (excess_operational_cost_ALL * 0.02)
    
    if i == 1:
        ax1.text(bar.get_x() + bar.get_width() / 2, y_pos, 
                 f'${bar.get_height():,.0f}\n({pct_gain:.1f}% of Potential)', 
                 ha='center', va='bottom', fontsize=12, fontweight='bold', color='green')
    else:
        ax1.text(bar.get_x() + bar.get_width() / 2, y_pos, 
                 f'${bar.get_height():,.0f}', ha='center', va='bottom', fontsize=12, fontweight='bold', color='black')


# Subplot 2: Operasyonel Kazanım
ax2 = plt.subplot(1, 2, 2)

plot_data_ops_gain = pd.DataFrame({
    'Metric': ['Total Unnecessary Movements', f'Movements Eliminated (Top {TOP_N_RELOCATION})'],
    'Count': [total_extra_picks_ALL, total_extra_picks_top_250]
})

bars_ops = sns.barplot(x='Metric', y='Count', data=plot_data_ops_gain, palette=['#34495E', '#2ECC71'], ax=ax2)

ax2.set_title('Operational Transformation: Movement Reduction', fontsize=15, fontweight='bold')
ax2.set_ylabel('Annual Unnecessary Movements (Units)', fontsize=12)
ax2.set_xlabel('')
ax2.tick_params(axis='x', rotation=15)

# Pick Count Etiketleri
for bar in bars_ops.patches:
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + (bar.get_height() * 0.03), 
             f'{bar.get_height():,.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')


plt.tight_layout()
plt.savefig('day7_top250_net_gain_v2.png')
# plt.show() 



# --- 7. PROFESYONEL ÇIKTI (TOP 250 KAZANIM) ---
print("\n" + "="*70)
print(f"✅ GÜN 7: TOP {TOP_N_RELOCATION} NET KAZANIM ANALİZİ (120 sn Fark):")
print("="*70)
print(f"Toplam Potansiyel Sistemsel Fazla Maliyet: ${excess_operational_cost_ALL:,.2f} USD")
print("-" * 35)

print(f"1. OPERASYONEL KAZANIM (Zaman/Hareket Tasarrufu):")
print(f"   Ortadan Kaldırılan Gereksiz Toplama Hareketi (Top {TOP_N_RELOCATION}): {total_extra_picks_top_250:,.0f} adet")
print(f"   Eşdeğer Yıllık Kazanılan İşgücü Zamanı: {total_extra_picks_top_250 * EXTRA_TIME_PER_PICK_SECONDS / 3600:,.1f} saat")
print("-" * 35)

print(f"2. FİNANSAL NET KAZANIM:")
print(f"   Tahmini YILLIK NET MALİYET TASARRUFU (Top {TOP_N_RELOCATION}): ${labor_cost_gain:,.2f} USD")
print(f"   Çözülen Sistemsel Fazla Maliyetin Yüzdesi: {pct_gain:.1f}%")
print(f"Yeni grafik 'day7_top250_net_gain_v2.png' olarak kaydedildi.")
print("="*70)