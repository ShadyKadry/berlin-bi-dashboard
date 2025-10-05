import pandas as pd
import os

# Ensure the raw data folder exists
os.makedirs("data/raw", exist_ok=True)

# Berlin open dataset (company register)
url = "https://datenregister.berlin.de/system/files/dataset/unternehmensregister.csv"

print("Downloading dataset from:", url)
df = pd.read_csv(url, sep=";", on_bad_lines="skip")
print(f"Loaded {len(df)} rows.")

# Save a local copy
df.to_csv("data/raw/berlin_companies.csv", index=False)
print("Saved raw data to data/raw/berlin_companies.csv")
