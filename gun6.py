import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# --- 0. Veri Yükleme ---
try:
    # Kullanıcının isteği üzerine dosya doğrudan 'inventory.csv' olarak okunuyor
    df = pd.read_csv('inventory.csv')
except FileNotFoundError:
    print("Hata: 'inventory.csv' dosyası bulunamadı. Lütfen dosya adını ve yolunu kontrol edin.")
    exit() 
except Exception as e:
    print(f"Hata: Dosya okunurken beklenmedik bir hata oluştu: {e}")
    exit()

# --- 1. ABC Sınıflandırması (Gün 5 Bağımlılığı) ---
df_abc = df.sort_values(by='Total_Cost', ascending=False).copy()
Total_Cost = df_abc['Total_Cost'].sum()
df_abc['Cum_Cost_Pct'] = (df_abc['Total_Cost'].cumsum() / Total_Cost) * 100

df_abc['ABC_Class'] = 'C'
df_abc.loc[df_abc['Cum_Cost_Pct'] <= 95, 'ABC_Class'] = 'B'
df_abc.loc[df_abc['Cum_Cost_Pct'] <= 80, 'ABC_Class'] = 'A'

# --- 2. Lokasyon Verimliliği Analizi (Gün 5 Bağımlılığı) ---
# Hızlı Erişim Tanımı: 'ZONEA', 'PZ' içeren veya '01' ile biten lokasyonlar.
if 'Location' in df_abc.columns:
    df_abc['Is_Fast_Access'] = df_abc['Location'].astype(str).str.contains('ZONEA', na=False, case=False) | \
                               df_abc['Location'].astype(str).str.contains('PZ', na=False, case=False) | \
                               df_abc['Location'].astype(str).str.contains('01$', na=False) 

    a_class_items = df_abc[df_abc['ABC_Class'] == 'A']
    total_a_items = len(a_class_items)
    a_in_fast_access_count = len(a_class_items[a_class_items['Is_Fast_Access'] == True])
    
    pct_a_in_fast_access = (a_in_fast_access_count / total_a_items) * 100 if total_a_items > 0 else 0
    pct_a_in_slow_access = 100 - pct_a_in_fast_access
else:
    print("Hata: 'Location' sütunu bulunamadı. Lokasyon verimliliği analizi yapılamıyor. Varsayılan değerler kullanılıyor.")
    pct_a_in_fast_access = 10.08 # Hata durumunda, daha önceki çalışmanızdan gelen değerleri kullanıyoruz
    pct_a_in_slow_access = 89.92
    
# --- 3. DAY 6 SIMÜLASYONU: Picking Maliyeti Etkisi ---

# Varsayımsal Operasyonel Veriler
daily_orders = 750 
avg_items_per_order = 8 
pct_a_in_orders = 0.40 # Siparişlerin %40'ı A-Sınıfı ürün içeriyor (varsayım)

distance_per_item_fast_access = 25 # metre
distance_per_item_slow_access = 60 # metre

picker_cost_hourly = 180.00 
avg_picking_speed_mps = 1.2 # metre/saniye
time_per_meter = 1.0 / avg_picking_speed_mps 

# Hesaplamalar
total_a_items_picked_daily = daily_orders * avg_items_per_order * pct_a_in_orders

# Mevcut Durum (A-Sınıfı %10.08 hızlı erişim)
a_items_fast_picked_current = total_a_items_picked_daily * (pct_a_in_fast_access / 100)
a_items_slow_picked_current = total_a_items_picked_daily * (pct_a_in_slow_access / 100)
current_total_picking_distance_a = \
    (a_items_fast_picked_current * distance_per_item_fast_access) + \
    (a_items_slow_picked_current * distance_per_item_slow_access)

# Optimize Edilmiş Durum (Hedef: A-Sınıfı %80 hızlı erişim)
target_pct_a_in_fast_access = 80
target_pct_a_in_slow_access = 20

a_items_fast_picked_optimized = total_a_items_picked_daily * (target_pct_a_in_fast_access / 100)
a_items_slow_picked_optimized = total_a_items_picked_daily * (target_pct_a_in_slow_access / 100)
optimized_total_picking_distance_a = \
    (a_items_fast_picked_optimized * distance_per_item_fast_access) + \
    (a_items_slow_picked_optimized * distance_per_item_slow_access)

# Elde Edilecek Tasarruflar
distance_saved_daily = current_total_picking_distance_a - optimized_total_picking_distance_a
time_saved_seconds = distance_saved_daily * time_per_meter
time_saved_hours = time_saved_seconds / 3600
cost_saved_daily = time_saved_hours * picker_cost_hourly
cost_saved_monthly = cost_saved_daily * 22 # Ortalama 22 iş günü

# --- 4. GÖRSELLEŞTİRME ---

# GRAFIK 1: Toplama Mesafesi Karşılaştırması
plt.figure(figsize=(10, 6))
sns.set_style("whitegrid")

plot_data_distance = pd.DataFrame({
    'Durum': ['Mevcut Durum', 'Optimize Edilmiş Durum (Hedef)'],
    'Mesafe (Metre)': [current_total_picking_distance_a, optimized_total_picking_distance_a]
})

bars_distance = sns.barplot(x='Durum', y='Mesafe (Metre)', data=plot_data_distance, palette=['#FF6347', '#4682B4']) # Kırmızımsı ve Mavimsi

plt.title('Gün 6: A Sınıfı Ürünler İçin Günlük Toplama Mesafesi Karşılaştırması', fontsize=16, fontweight='bold')
plt.ylabel('Günlük Toplama Mesafesi (Metre)', fontsize=12)
plt.xlabel('')

for bar in bars_distance.patches:
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + (bars_distance.get_ylim()[1]*0.01),
             f'{bar.get_height():,.0f} m', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.show() # Grafik 1'i göster
print("Grafik 1: Toplama Mesafesi Karşılaştırması oluşturuldu.")

# GRAFIK 2: Potansiyel Aylık İş Gücü Maliyeti Tasarrufu
plt.figure(figsize=(8, 5))
sns.set_style("whitegrid")

plot_data_cost = pd.DataFrame({
    'Metrik': ['Potansiyel Aylık Tasarruf'],
    'Maliyet (TL)': [cost_saved_monthly]
})

bars_cost = sns.barplot(x='Metrik', y='Maliyet (TL)', data=plot_data_cost, palette='Greens_r') # Yeşil tonlar tasarrufu vurgular

plt.title('Gün 6: Potansiyel Aylık İş Gücü Maliyeti Tasarrufu', fontsize=16, fontweight='bold')
plt.ylabel('Aylık Maliyet Tasarrufu (TL)', fontsize=12)
plt.xlabel('')
plt.xticks([]) 

for bar in bars_cost.patches:
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2, 
             f'₺{bar.get_height():,.0f}', ha='center', va='center', fontsize=18, color='white', fontweight='bold')

plt.tight_layout()
plt.show() # Grafik 2'yi göster
print("Grafik 2: Aylık İş Gücü Maliyeti Tasarrufu oluşturuldu.")

# --- 5. KONSOL ÇIKTISI (Verilerinizi Kontrol Etmek İçin) ---
print("\n" + "="*50)
print("✅ DAY 6 ANALYSIS SUMMARY (Picking Cost Impact & Optimization):")
print(f"A-Class Fast Access Percentage (Actual): {pct_a_in_fast_access:.2f}%")
print("-" * 25)
print(f"Current Daily Picking Distance (A-Class Items): {current_total_picking_distance_a:,.0f} meters")
print(f"Optimized Daily Picking Distance (Target 80% Fast Access): {optimized_total_picking_distance_a:,.0f} meters")
print("-" * 25)
print(f"Potential Daily Distance Saved: {distance_saved_daily:,.0f} meters")
print(f"Potential Daily Time Saved: {time_saved_hours:.2f} hours")
print(f"Potential Daily Labor Cost Savings: {cost_saved_daily:.2f} ₺")
print(f"Potential MONTHLY Labor Cost Savings: {cost_saved_monthly:,.0f} ₺")
print("="*50)