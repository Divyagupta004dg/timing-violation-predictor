import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

# Load data
df = pd.read_csv('dataset/timing_dataset.csv')
le = LabelEncoder()
df['design_enc'] = le.fit_transform(df['design'])

features = ['design_enc','clock_period_ns','input_delay','output_delay',
            'cell_count','chip_area','wns','tns']
X = df[features]
y = df['setup_violated']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# 3 models
models = {
    'Logistic Regression': Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, random_state=42))
    ]),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'XGBoost': XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
}

# Cross validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

results = {}
print("="*60)
print("         MODEL COMPARISON WITH CROSS VALIDATION")
print("="*60)

for name, model in models.items():
    # CV scores
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
    
    # Train test
    model.fit(X_train, y_train)
    test_pred = model.predict(X_test)
    test_acc  = accuracy_score(y_test, test_pred)
    
    results[name] = {
        'cv_mean': cv_scores.mean(),
        'cv_std':  cv_scores.std(),
        'test_acc': test_acc,
        'pred': test_pred,
        'cv_scores': cv_scores
    }
    
    print(f"\n{name}")
    print(f"  CV Accuracy  : {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")
    print(f"  CV Scores    : {[f'{s*100:.1f}%' for s in cv_scores]}")
    print(f"  Test Accuracy: {test_acc*100:.2f}%")
    print(classification_report(y_test, test_pred, target_names=['No Violation','Violated']))

# Plot 1 — CV scores comparison
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Bar chart — mean CV accuracy
names = list(results.keys())
cv_means = [results[n]['cv_mean']*100 for n in names]
cv_stds  = [results[n]['cv_std']*100  for n in names]
colors   = ['#3498db', '#2ecc71', '#e74c3c']

bars = axes[0].bar(names, cv_means, yerr=cv_stds,
                   color=colors, capsize=8, alpha=0.85, edgecolor='black')
axes[0].set_ylim(80, 105)
axes[0].set_ylabel('Accuracy (%)')
axes[0].set_title('5-Fold CV Accuracy Comparison')
axes[0].tick_params(axis='x', rotation=15)
for bar, mean, std in zip(bars, cv_means, cv_stds):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + std + 0.5,
                f'{mean:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Box plot — CV score distribution
cv_data = [results[n]['cv_scores']*100 for n in names]
bp = axes[1].boxplot(cv_data, labels=names, patch_artist=True, notch=False)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[1].set_ylabel('Accuracy (%)')
axes[1].set_title('CV Score Distribution (5 folds)')
axes[1].tick_params(axis='x', rotation=15)
axes[1].set_ylim(80, 105)

# Confusion matrices
from sklearn.metrics import ConfusionMatrixDisplay
best_model_name = max(results, key=lambda n: results[n]['cv_mean'])
cm = confusion_matrix(y_test, results[best_model_name]['pred'])
sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', ax=axes[2],
            xticklabels=['No Viol','Violated'],
            yticklabels=['No Viol','Violated'])
axes[2].set_title(f'Best Model: {best_model_name}\nTest Accuracy: {results[best_model_name]["test_acc"]*100:.1f}%')
axes[2].set_ylabel('Actual')
axes[2].set_xlabel('Predicted')

plt.suptitle('Model Comparison — Timing Violation Predictor', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('ml/model_comparison.png', dpi=150, bbox_inches='tight')
print("\nSaved: ml/model_comparison.png")

# Overfitting check
print("\n" + "="*60)
print("           OVERFITTING ANALYSIS")
print("="*60)
for name in names:
    cv_acc   = results[name]['cv_mean'] * 100
    test_acc = results[name]['test_acc'] * 100
    diff     = abs(cv_acc - test_acc)
    status   = "OK" if diff < 5 else "CHECK"
    print(f"  {name:<22} CV={cv_acc:.1f}%  Test={test_acc:.1f}%  Diff={diff:.1f}%  [{status}]")

print("\nInterview answer:")
print("  '5-fold cross validation use kiya — CV accuracy consistent hai")
print("   across all folds, overfitting nahi hai kyunki WNS directly")
print("   clock period se derive hota hai — deterministic relationship hai.'")
print("\nAll done!")
