import pandas as pd
import matplotlib.pyplot as plt

df1 = pd.read_csv("results/MILP_final4.csv")
df2 = pd.read_csv("results/Lagrangian_final4.csv")
df3 = pd.read_csv("results/ADMM2.csv") 

def summarize(df):
    return df.groupby("num_trains")["time"].agg(mean="mean", std="std")

milp = summarize(df1)
lr = summarize(df2)
admm = summarize(df3)
plt.figure()

# MILP
plt.errorbar(milp.index,milp["mean"], yerr=milp["std"], marker="o", capsize=4, label="MILP")
# LR
plt.errorbar(lr.index, lr["mean"], yerr=lr["std"], marker="o", capsize=4, label="LR")
# ADMM
plt.errorbar(admm.index, admm["mean"], yerr=admm["std"], marker="o", capsize=4, label="ADMM")

plt.xlabel("Number of trains")
plt.ylabel("Average runtime (seconds)")
plt.yscale("log")

plt.xticks([5, 10, 15, 20])

plt.legend()
plt.tight_layout()
plt.savefig("MILP_LR_ADMM.png", dpi=300)
plt.close()