"""
NLP Classifier for Dispatcher Remarks (Agent 3 - Analyst)
Classifies free-text remarks into standardized cause categories with confidence scores.
Enforces Rule 3 (Brain.md): Confidence < 0.6 flagged as 'needs_review'.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

class CurtailmentRemarkClassifier:
    def __init__(self, confidence_threshold=0.60):
        self.confidence_threshold = confidence_threshold
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=1000, stop_words='english')),
            ('clf', LogisticRegression(C=1.0, max_iter=500, class_weight='balanced'))
        ])
        self.is_trained = False
        
    def train_and_evaluate(self, df):
        print("[Analyst Agent] Training NLP cause classifier...")
        X = df['dispatcher_remark']
        y = df['true_cause_label']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.pipeline.fit(X_train, y_train)
        self.is_trained = True
        
        y_pred = self.pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        
        report = classification_report(y_test, y_pred, output_dict=True)
        cm = confusion_matrix(y_test, y_pred)
        
        print(f"[Analyst Agent] Classifier Training Complete. Test Accuracy: {acc * 100:.2f}%")
        return {
            "accuracy": acc,
            "report": report,
            "confusion_matrix": cm,
            "test_size": len(y_test)
        }
        
    def predict_events(self, df):
        if not self.is_trained:
            raise ValueError("Classifier must be trained before running predictions.")
            
        X = df['dispatcher_remark']
        probs = self.pipeline.predict_proba(X)
        classes = self.pipeline.classes_
        
        predicted_causes = []
        confidence_scores = []
        pipeline_statuses = []
        validation_statuses = []
        
        for i, prob_dist in enumerate(probs):
            max_idx = np.argmax(prob_dist)
            pred_cause = classes[max_idx]
            conf = float(prob_dist[max_idx])
            
            predicted_causes.append(pred_cause)
            confidence_scores.append(round(conf, 3))
            
            # Brain Rule 3: Low confidence -> needs_review
            if conf < self.confidence_threshold:
                pipeline_statuses.append("needs_review")
            else:
                pipeline_statuses.append("classified")
                
            # Brain Rule 1: Cross validation check
            dev = df.iloc[i]['deviation_mw']
            curt = df.iloc[i]['curtailed_mw']
            if abs(dev - curt) < 5.0:
                validation_statuses.append("confirmed")
            else:
                validation_statuses.append("mismatch")
                
        df_out = df.copy()
        df_out['predicted_cause'] = predicted_causes
        df_out['confidence_score'] = confidence_scores
        df_out['pipeline_status'] = pipeline_statuses
        df_out['validation_status'] = validation_statuses
        
        return df_out

def run_classifier_pipeline(input_csv="data/processed/synthetic_curtailment_events.csv",
                            output_csv="data/processed/classified_curtailment_events.csv"):
    if not os.path.exists(input_csv):
        from agents.analyst.synthetic_data_generator import generate_synthetic_data
        df_raw = generate_synthetic_data(output_path=input_csv)
    else:
        df_raw = pd.read_csv(input_csv)
        
    classifier = CurtailmentRemarkClassifier()
    metrics = classifier.train_and_evaluate(df_raw)
    
    df_classified = classifier.predict_events(df_raw)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_classified.to_csv(output_csv, index=False)
    print(f"[Analyst Agent] Saved classified results to '{output_csv}'.")
    return classifier, metrics, df_classified

def get_filtered_events(df: pd.DataFrame, region=None, state=None, cause=None, validation_status=None, min_confidence=0.0, limit=None, offset=0):
    """Filters curtailment events. Logic moved here from API layer."""
    if region:
        df = df[df['region'].str.lower() == region.lower()]
    if state:
        df = df[df['state'].str.lower() == state.lower()]
    if cause:
        df = df[df['predicted_cause'].str.lower() == cause.lower()]
    if validation_status:
        df = df[df['validation_status'].str.lower() == validation_status.lower()]
    if min_confidence > 0.0:
        df = df[df['confidence_score'] >= min_confidence]
        
    total_count = len(df)
    
    if limit is not None:
        paginated_df = df.iloc[offset:offset+limit]
    else:
        paginated_df = df.iloc[offset:]
        
    return total_count, paginated_df

if __name__ == "__main__":
    run_classifier_pipeline()
