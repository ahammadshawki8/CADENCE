"""Check whether task types are confounded with the PD/HC label.

If a task is performed by only one class, a model trained on it would learn the
task, not the disease. We want tasks that BOTH classes performed, ideally by most
speakers, so comparisons are like-with-like.
"""
import pandas as pd
from config import DATA_DIR

df = pd.read_parquet(DATA_DIR / "index_italian.parquet")
df["lab"] = df.label.map({0: "HC", 1: "PD"})

print("== speakers performing each task, by class ==")
piv = (df.groupby(["task", "lab"]).speaker.nunique()
         .unstack(fill_value=0).assign(total=lambda d: d.sum(axis=1)))
print(piv.sort_values("total", ascending=False))

print("\n== files per task, by class ==")
print(df.groupby(["task", "lab"]).size().unstack(fill_value=0))

print("\n== total speakers per class ==")
print(df.groupby("lab").speaker.nunique())

# Which tasks are done by (nearly) all speakers of BOTH classes?
n_hc = df[df.lab == "HC"].speaker.nunique()
n_pd = df[df.lab == "PD"].speaker.nunique()
cov = df.groupby(["task", "lab"]).speaker.nunique().unstack(fill_value=0)
cov["hc_cov"] = (cov.get("HC", 0) / n_hc).round(2)
cov["pd_cov"] = (cov.get("PD", 0) / n_pd).round(2)
print("\n== task coverage (fraction of each class's speakers) ==")
print(cov[["hc_cov", "pd_cov"]].sort_values("hc_cov", ascending=False))
