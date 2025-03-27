import pandas as pd

# Load dataset
df = pd.read_csv("dataset.csv")  # Ensure this file exists

# Rename columns to match model expectations
df.rename(columns={"URL": "url", "Type": "label"}, inplace=True)

# Save the updated dataset
df.to_csv("dataset.csv", index=False)

print("✅ Dataset columns fixed! You can now retrain the model.")
