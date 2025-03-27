import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

# Load the dataset (Replace with the correct filename)
DATASET_PATH = "dataset.csv"  # Ensure this is the correct filename

# Load the dataset
df = pd.read_csv(DATASET_PATH)

# Assuming the dataset has columns: 'url' and 'label'
# 'url' contains the website URLs, 'label' contains 0 (Safe) and 1 (Malicious)
if 'url' not in df.columns or 'label' not in df.columns:
    raise ValueError("Dataset must contain 'url' and 'label' columns!")

# Convert text URLs to numerical features using TF-IDF
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['url'])  # Convert URLs to TF-IDF features
y = df['label']  # Labels: 0 (Safe), 1 (Malicious)

# Split dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a RandomForest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save the trained model
joblib.dump(model, "model.pkl")  # Save the model
joblib.dump(vectorizer, "vectorizer.pkl")  # Save the vectorizer

print("Model training complete. 'model.pkl' and 'vectorizer.pkl' saved!")
