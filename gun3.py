import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------------------
# 1) Veri Yükleme
# -----------------------------------------
df = pd.read_csv("outbound_movements.csv")

# -----------------------------------------
# 2) Kolonları doğru tipe çevirme
# -----------------------------------------
df["Document_Date"] = pd.to_datetime(df["Document_Date"])
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")

# -----------------------------------------
# 3) SKU (Material_ID) bazında talep istatistikleri
# -----------------------------------------
summary = df.groupby("Material_ID")["Quantity"].agg(["mean", "std"]).reset_index()
summary["cv"] = summary["std"] / summary["mean"]

# 0'a bölme ve NaN temizliği
summary = summary.dropna()
summary = summary[summary["mean"] > 0]

# -----------------------------------------
# 4) Top 10 riskli SKU (CV yüksek)
# -----------------------------------------
top10_risk = summary.sort_values("cv", ascending=False).head(10)

# -----------------------------------------
# 5) Scatter Plot
# -----------------------------------------
plt.figure(figsize=(12, 7))

# Risk ve stabil bölgeleri renklendir
colors = summary["cv"].apply(lambda x: 'red' if x > 1 else 'green')
plt.scatter(summary["mean"], summary["cv"], c=colors, s=45, alpha=0.7)

# CV = 1 eşik çizgisi
plt.axhline(y=1, linestyle="--", color='black', linewidth=1)
plt.text(summary["mean"].max()*0.7, 1.05, "CV = 1 Eşiği", fontsize=10, color='black')

# Top 10 riskli SKU isimlerini grafikte göster
for _, row in top10_risk.iterrows():
    plt.text(row["mean"], row["cv"] + 0.03, row["Material_ID"], fontsize=9, ha='center')

# Axes ve log scale
plt.xscale('log')
plt.xlabel("Average Demand (Mean)")
plt.ylabel("Demand Variability (CV)")
plt.title("SKU-Based Demand Variability (Mean vs CV)")

plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
