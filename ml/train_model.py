import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

df = pd.read_csv('dataset/timing_dataset.csv')
print("Dataset shape:", df.shape)
print("\nDesign distribution:")
print(df['design'].value_counts())
print("\nClass distribution:")
print(df['setup_violated'].value_counts())

le = LabelEncoder()
df['design_enc'] = le.fit_transform(df['design'])

features = ['design_enc','clock_period_ns','input_delay','output_delay','cell_count','chip_area','wns','tns']
X = df[features]
y = df['setup_violated']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_acc = accuracy_score(y_test, rf_pred)
print(f"\n=== Random Forest ===")
print(f"Accuracy: {rf_acc*100:.2f}%")
print(classification_report(y_test, rf_pred))

xgb = XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
xgb.fit(X_train, y_train)
xgb_pred = xgb.predict(X_test)
xgb_acc = accuracy_score(y_test, xgb_pred)
print(f"=== XGBoost ===")
print(f"Accuracy: {xgb_acc*100:.2f}%")
print(classification_report(y_test, xgb_pred))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
rf_imp = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=True)
rf_imp.plot(kind='barh', ax=axes[0], color='steelblue')
axes[0].set_title('Random Forest - Feature Importance')
axes[0].set_xlabel('Importance Score')
xgb_imp = pd.Series(xgb.feature_importances_, index=features).sort_values(ascending=True)
xgb_imp.plot(kind='barh', ax=axes[1], color='darkorange')
axes[1].set_title('XGBoost - Feature Importance')
axes[1].set_xlabel('Importance Score')
plt.tight_layout()
plt.savefig('ml/feature_importance.png', dpi=150)
print("\nSaved: ml/feature_importance.png")

fig2, axes2 = plt.subplots(1, 2, figsize=(10, 4))
sns.heatmap(confusion_matrix(y_test, rf_pred), annot=True, fmt='d',
            cmap='Blues', ax=axes2[0],
            xticklabels=['No Viol','Violated'],
            yticklabels=['No Viol','Violated'])
axes2[0].set_title(f'Random Forest (Acc: {rf_acc*100:.1f}%)')
axes2[0].set_ylabel('Actual')
axes2[0].set_xlabel('Predicted')
sns.heatmap(confusion_matrix(y_test, xgb_pred), annot=True, fmt='d',
            cmap='Oranges', ax=axes2[1],
            xticklabels=['No Viol','Violated'],
            yticklabels=['No Viol','Violated'])
axes2[1].set_title(f'XGBoost (Acc: {xgb_acc*100:.1f}%)')
axes2[1].set_ylabel('Actual')
axes2[1].set_xlabel('Predicted')
plt.tight_layout()
plt.savefig('ml/confusion_matrix.png', dpi=150)
print("Saved: ml/confusion_matrix.png")

print("\n=== Per-Design Accuracy (Random Forest) ===")
df_test = X_test.copy()
df_test['actual'] = y_test.values
df_test['predicted'] = rf_pred
df_test['design'] = le.inverse_transform(df_test['design_enc'].astype(int))
for d in df_test['design'].unique():
    subset = df_test[df_test['design'] == d]
    acc = accuracy_score(subset['actual'], subset['predicted'])
    print(f"  {d}: {acc*100:.1f}%")

print("\n=== Minimum Safe Clock Per Design ===")
print(f"{'Design':>16} | {'Input Delay':>11} | {'Min Safe Clock':>14}")
print("-" * 48)
for design_name in df['design'].unique():
    design_df = df[df['design'] == design_name]
    for delay in [0.2, 1.0, 2.0]:
        safe = design_df[
            (abs(design_df['input_delay'] - delay) < 0.01) &
            (design_df['setup_violated'] == 0)
        ]['clock_period_ns'].min()
        if pd.isna(safe):
            print(f"{design_name:>16} | {delay:>11.1f} | {'Always fails':>14}")
        else:
            print(f"{design_name:>16} | {delay:>11.1f} | {safe:>14.1f} ns")

print("\nAll done!")
import joblib

joblib.dump(rf, "ml/rf_model.pkl")
joblib.dump(xgb, "ml/xgb_model.pkl")

print("Models saved successfully")
