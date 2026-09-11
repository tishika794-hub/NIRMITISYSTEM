"""
core/ml/trainer.py
Trains the XGBoost model on the downloaded historical climate dataset.
"""
import os
import json
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support

CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(CORE_DIR, "data", "dataset", "training_dataset.csv")
MODELS_DIR = os.path.join(CORE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_NAMES = [
    "rain_1h", "rain_3h", "rain_6h", "rain_24h", "rain_72h",
    "rain_intensity", "rain_acceleration", "soil_moisture_surface",
    "soil_saturation_index", "antecedent_rain_48h", "elevation_m", "slope_deg"
]

def train_on_downloaded_data():
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: {CSV_PATH} not found. Run download_all_data.py first!")
        return

    print("⏳ Loading real historical dataset and training XGBoost...")
    df = pd.read_csv(CSV_PATH)
    
    X = df[FEATURE_NAMES]
    y = df["flood_event"]
    
    # 80% Train, 20% Test Split
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    model = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.03,
        scale_pos_weight=2.2,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluate performance
    probs = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probs)
    preds = (probs >= 0.50).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(y_test, preds, average="binary")
    
    print("\n" + "="*50)
    print("🏆 REAL MODEL PERFORMANCE ON TEST DATA:")
    print(f"• ROC-AUC Score : {auc:.4f} (>90% indicates elite discrimination)")
    print(f"• Recall Rate   : {r*100:.1f}% (High disaster capture rate)")
    print(f"• Precision     : {p*100:.1f}% (Low false alarms)")
    print(f"• F1-Score      : {f1:.4f}")
    print("="*50)
    
    # Save Model Artifacts
    model_file = os.path.join(MODELS_DIR, "xgboost_flood_model.json")
    model.save_model(model_file)
    
    metadata = {
        "features": FEATURE_NAMES,
        "test_roc_auc": round(auc, 4),
        "test_recall": round(r, 4),
        "test_precision": round(p, 4),
        "test_f1": round(f1, 4)
    }
    with open(os.path.join(MODELS_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"💾 Saved trained AI model to: {model_file}")

if __name__ == "__main__":
    train_on_downloaded_data()

