import pandas as pd
import matplotlib.pyplot as plt

df1 = pd.read_csv("results/MILP_final.csv")
df2 = pd.read_csv("results/Lagrangian_final.csv")

def summarize(df):
    return df.groupby("num_trains")["time"].agg(mean="mean", std="std")

milp = summarize(df1)
lr = summarize(df2)
plt.figure()

# MILP
plt.errorbar(milp.index,milp["mean"], yerr=milp["std"], marker="o", capsize=4, label="MILP")
# LR
plt.errorbar(lr.index, lr["mean"], yerr=lr["std"], marker="o", capsize=4, label="LR")

plt.xlabel("Number of trains")
plt.ylabel("Average runtime (seconds)")
plt.yscale("log")

plt.xticks([5, 10, 15, 20])

plt.legend()
plt.tight_layout()
plt.savefig("MILP_LR.png", dpi=300)
plt.close()