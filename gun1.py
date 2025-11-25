import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import locale
import numpy as np

# Türkçe yerel ayarı
try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Turkish_Turkey.1254')
    except locale.Error:
        print("Uyarı: Türkçe yerel ayar ayarlanamadı. Para birimi formatı varsayılan kalacak.")

# CSV yükleme
try:
    df = pd.read_csv('inventory.csv')
except FileNotFoundError:
    print("inventory.csv dosyası bulunamadı.")
    exit()

df['Last_Movement_Date'] = pd.to_datetime(df['Last_Movement_Date'])
current_date = datetime(2025, 11, 19)

# --- 0. Toplam Stok Maliyeti ---
total_stock_cost = df['Total_Cost'].sum()
formatted_total_cost = locale.currency(total_stock_cost, grouping=True, symbol='₺')

# --- 1. Güvenlik Stoğu İhlalleri ---
safety_stock_violations = df[df['Stock_Qty'] < df['Safety_Stock']].shape[0]
total_sku_count = df.shape[0]
violation_percentage = (safety_stock_violations / total_sku_count) * 100

# --- 2. Yavaş Hareket Eden Stok (180+ Gün) ---
days_since_last_movement = (current_date - df['Last_Movement_Date']).dt.days
slow_moving_stock_count = df[days_since_last_movement > 180].shape[0]
slow_moving_percentage = (slow_moving_stock_count / total_sku_count) * 100

# --- 3. SKU Yoğunlaşması (63% Maliyet) ---
df_sorted = df.sort_values(by='Total_Cost', ascending=False)
df_sorted['Cumulative_Cost'] = df_sorted['Total_Cost'].cumsum()
target_cost = df_sorted['Total_Cost'].sum() * 0.63
sku_concentration = df_sorted[df_sorted['Cumulative_Cost'] <= target_cost].shape[0]
concentration_percentage = (sku_concentration / total_sku_count) * 100

# --- 4. Warehouse Bazında Stok Değeri (TL) ---
warehouse_stock_cost = df.groupby('Warehouse')['Total_Cost'].sum()
warehouse_names = warehouse_stock_cost.index
warehouse_values = warehouse_stock_cost.values

# --- Grafik Oluşturma ---
fig, axs = plt.subplots(2, 2, figsize=(16, 12))

# 1. Güvenlik Stoğu İhlalleri
axs[0,0].bar(['Güvenlik Stoğu İhlali'], [violation_percentage], color='#1f77b4')
axs[0,0].set_ylim(0,100)
axs[0,0].set_ylabel('Oran (%)')
for i, v in enumerate([violation_percentage]):
    axs[0,0].text(i, v+1, f'{v:.2f}%', ha='center', fontweight='bold')

# 2. Yavaş Hareket Eden Stok
axs[0,1].bar(['180+ Gün Hareketsiz Stok'], [slow_moving_percentage], color='#ff7f0e')
axs[0,1].set_ylim(0,100)
axs[0,1].set_ylabel('Oran (%)')
for i, v in enumerate([slow_moving_percentage]):
    axs[0,1].text(i, v+1, f'{v:.2f}%', ha='center', fontweight='bold')

# 3. SKU Yoğunlaşması
axs[1,0].bar(['%63 Maliyeti Oluşturan SKU'], [concentration_percentage], color='#2ca02c')
axs[1,0].set_ylim(0,100)
axs[1,0].set_ylabel('Oran (%)')
for i, v in enumerate([concentration_percentage]):
    axs[1,0].text(i, v+1, f'{v:.2f}%', ha='center', fontweight='bold')

# 4. Warehouse Bazında Stok Değeri (TL)
axs[1,1].bar(warehouse_names, warehouse_values, color='#38b6ff')
axs[1,1].set_ylabel('Stok Değeri (₺)')
for i, v in enumerate(warehouse_values):
    axs[1,1].text(i, v + max(warehouse_values)*0.01, f"{locale.currency(v, grouping=True, symbol='₺')}", 
                   ha='center', fontweight='bold', fontsize=10)

# Genel başlık ve toplam maliyet alt başlığı
plt.suptitle(f'Gün 1: Operasyonel Risk ve Maliyet Metrikleri\nToplam Stok Maliyeti: {formatted_total_cost}', fontsize=16, fontweight='bold')
plt.tight_layout(rect=[0,0,1,0.95])

plt.savefig('gun1_stok_analizi_grafigi.png')
plt.show()

print("-"*50)
print(f"✅ Analiz Başarılı.")
print(f"Toplam Stok Maliyeti: {formatted_total_cost}")
print(f"Grafik 'gun1_stok_analizi_grafigi.png' olarak kaydedildi.")
print("-"*50)