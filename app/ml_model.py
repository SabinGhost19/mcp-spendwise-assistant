import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pickle
import os

class TransactionCategorizer:
    def __init__(self, n_categories=6):
        self.n_categories = n_categories
        self.vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2), lowercase=True)
        self.kmeans = KMeans(n_clusters=n_categories, random_state=42, n_init=10)
        self.cluster_to_category = {}
        self.is_trained = False
    
    def preprocess_description(self, description: str) -> str:
        text = description.lower()
        text = ''.join(char for char in text if char.isalpha() or char.isspace())
        return ' '.join(text.split())
    
    def train(self, transactions_df: pd.DataFrame) -> dict:
        df = transactions_df.copy()
        df['clean_description'] = df['description'].apply(self.preprocess_description)
        df = df.dropna(subset=['category', 'clean_description'])
        
        if len(df) < self.n_categories:
            return {"success": False, "message": f"Prea puține date. Minim {self.n_categories} necesare."}
        
        X = self.vectorizer.fit_transform(df['clean_description'])
        self.kmeans.fit(X)
        df['cluster'] = self.kmeans.labels_
        
        for cluster_id in range(self.n_categories):
            cluster_data = df[df['cluster'] == cluster_id]
            if len(cluster_data) > 0:
                self.cluster_to_category[cluster_id] = cluster_data['category'].mode()[0]
        
        self.is_trained = True
        return {"success": True, "message": f"Model antrenat pe {len(df)} tranzacții", "clusters": len(self.cluster_to_category)}
    
    def predict(self, description: str) -> str:
        if not self.is_trained:
            return "Other"
        clean_desc = self.preprocess_description(description)
        X = self.vectorizer.transform([clean_desc])
        cluster_id = self.kmeans.predict(X)[0]
        return self.cluster_to_category.get(cluster_id, "Other")
    
    def save(self, filepath: str):
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(filepath: str):
        with open(filepath, 'rb') as f:
            return pickle.load(f)
