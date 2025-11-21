import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

# Dosyanızı okuyun
try:
    df = pd.read_csv('inventory.csv')
except FileNotFoundError:
    print("inventory.csv dosyası bulunamadı. Lütfen dosya adını kontrol edin.")
    exit()

# 1. ABC Sınıflandırması (Gün 2 Tekrarı - A ve C sınıfı ürünleri bulmak için)
df_abc = df.sort_values(by='Total_Cost', ascending=False).copy()
Total_Cost = df_abc['Total_Cost'].sum()
df_abc['Cum_Cost_Pct'] = (df_abc['Total_Cost'].cumsum() / Total_Cost) * 100

# 2. Örnek SKU'ları Seçme
# En yüksek maliyetli A Sınıfı ürün
sku_a = df_abc.iloc[0] 
# En düşük maliyetli C Sınıfı ürün
sku_c = df_abc.iloc[-1] 

# 3. Güvenlik Stoğu Parametrelerini Simüle Etme (Gerçek veriye dayalı olmadığı için varsayımsal)
# Amaç: İki ürünün de talebi biraz değişken olsun, A ürünü daha az değişken (daha profesyonel yönetiliyor)
# Bu analiz için kritik parametre: Unit_Cost (Birim Maliyet)
 
# Z-skorları (Service Level - Hizmet Seviyesi)
sl_low = 0.90  # Düşük Öncelik (C Sınıfı için ideal)
sl_high = 0.98 # Yüksek Öncelik (A Sınıfı için ideal)
z_low = norm.ppf(sl_low)  # Örn: 1.28
z_high = norm.ppf(sl_high) # Örn: 2.05

# Talep Değişkenliği (Std Dev x Köklü Lead Time) Simülasyonu
# A Sınıfı: Düşük değişkenlik (CV düşük)
demand_dev_a = 50 
# C Sınıfı: Yüksek değişkenlik (CV yüksek)
demand_dev_c = 85 

# 4. Güvenlik Stoğu (SS) ve Kilitlenen Sermayeyi Hesaplama
def calculate_ss_cost(sku, z_score, demand_dev):
    ss = z_score * demand_dev
    ss_cost = ss * sku['Unit_Cost']
    return ss, ss_cost

# A Sınıfı Hesaplamalar
ss_a_low, cost_a_low = calculate_ss_cost(sku_a, z_low, demand_dev_a)
ss_a_high, cost_a_high = calculate_ss_cost(sku_a, z_high, demand_dev_a)

# C Sınıfı Hesaplamalar
ss_c_low, cost_c_low = calculate_ss_cost(sku_c, z_low, demand_dev_c)
ss_c_high, cost_c_high = calculate_ss_cost(sku_c, z_high, demand_dev_c)


# 5. Grafik için Veri Yapılandırma
data = {
    'SKU': [sku_a['Material_ID'] + ' (A-Class)', sku_c['Material_ID'] + ' (C-Class)'], # Burada İngilizce
    'Unit_Cost': [sku_a['Unit_Cost'], sku_c['Unit_Cost']],
    'SS_Cost_90': [cost_a_low, cost_c_low],
    'SS_Cost_98': [cost_a_high, cost_c_high]
}
df_plot = pd.DataFrame(data)

# 6. Görselleştirme (Kilitlenen Sermaye Karşılaştırması)
x = np.arange(len(df_plot)) 
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))

rects1 = ax.bar(x - width/2, df_plot['SS_Cost_90'], width, label='SL 90% (Lower Risk)', color='#1f77b4') # Burada İngilizce
rects2 = ax.bar(x + width/2, df_plot['SS_Cost_98'], width, label='SL 98% (Higher Risk)', color='#ff7f0e') # Burada İngilizce

# Başlık ve Etiketler
ax.set_ylabel('Capital Locked Value (TL)', fontsize=12) # Burada İngilizce
ax.set_title('Safety Stock Capital Locked by Service Level', fontsize=14, fontweight='bold') # Burada İngilizce
ax.set_xticks(x)
ax.set_xticklabels(df_plot['SKU'])
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Bar üzerine değerleri yazma
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:,.0f} ₺',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)

plt.tight_layout()
plt.savefig('gun4_ss_maliyet_etkisi.png')
plt.show()

print("\n" + "="*50)
print("✅ ANALYSIS SUMMARY (Safety Stock Cost Impact):")
print(f"A-Class Item ({sku_a['Material_ID']} Unit Cost: {sku_a['Unit_Cost']:.2f} ₺)")
print(f" - Capital Locked for SL 90%: {cost_a_low:,.0f} ₺")
print(f" - Capital Locked for SL 98%: {cost_a_high:,.0f} ₺ (Increase: {cost_a_high - cost_a_low:,.0f} ₺)")
print("-" * 25)
print(f"C-Class Item ({sku_c['Material_ID']} Unit Cost: {sku_c['Unit_Cost']:.2f} ₺)")
print(f" - Capital Locked for SL 90%: {cost_c_low:,.0f} ₺")
print(f" - Capital Locked for SL 98%: {cost_c_high:,.0f} ₺ (Increase: {cost_c_high - cost_c_low:,.0f} ₺)")
print("Chart saved as 'gun4_ss_maliyet_etkisi.png'.")
print("="*50)