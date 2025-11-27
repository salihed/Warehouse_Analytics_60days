import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# CSV'den veri okuma
df = pd.read_csv("outbound_movements.csv", parse_dates=["Document_Date"])

# 15 dakikalık slot ile zaman serisi oluştur
df['TimeSlot'] = df['Document_Date'].dt.floor('15T')
time_series = df.groupby('TimeSlot').size()

# Basit anomaly detection (3 sigma method)
mean_val = time_series.mean()
std_val = time_series.std()
anomalies = time_series[time_series > mean_val + 3*std_val]

# Heatmap için pivot table (day vs hour)
df['Day'] = df['Document_Date'].dt.day_name()
df['Hour'] = df['Document_Date'].dt.hour
heatmap_data = df.pivot_table(index='Hour', columns='Day', values='Movement_ID', aggfunc='count').fillna(0)

# Tek figure içinde iki grafiği çiz
fig, axes = plt.subplots(2, 1, figsize=(16, 10), constrained_layout=True)

# Zaman serisi + anomaly
axes[0].plot(time_series.index, time_series.values, color='blue', label='Outbound Movements')
axes[0].scatter(anomalies.index, anomalies.values, color='red', label='Anomalies')
axes[0].set_title('DAY7: Peak Hour Bottleneck Analysis\nOutbound Movements with Anomalies')
axes[0].set_ylabel('Movements per 15-min slot')
axes[0].legend()
axes[0].grid(True)

# Heatmap
sns.heatmap(heatmap_data, ax=axes[1], cmap='Reds', cbar_kws={'label': 'Number of Movements'})
axes[1].set_title('DAY7: Hourly Heatmap with Anomalies')
axes[1].set_xlabel('Day of Week')
axes[1].set_ylabel('Hour of Day')

plt.show()
