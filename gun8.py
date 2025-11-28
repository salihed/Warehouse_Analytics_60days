import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# CSV yükle
df = pd.read_csv("inventory.csv", parse_dates=["Goods_Receipt_Date", "Last_Movement_Date"])

# Stokta geçen gün sayısı
df["Days_in_Stock"] = (datetime.now() - df["Goods_Receipt_Date"]).dt.days

# Heatmap için veri hazırlığı
heatmap_data = df.groupby(["Warehouse","ABC_Class"]).agg(Avg_Days=("Days_in_Stock","mean")).unstack()
plt.figure(figsize=(10,6))
sns.heatmap(heatmap_data["Avg_Days"], annot=True, fmt=".1f", cmap="YlOrRd")
plt.title("DAY8: Warehouse vs ABC Class - Average Days in Stock")
plt.ylabel("Warehouse")
plt.xlabel("ABC Class")
plt.tight_layout()
plt.show()
