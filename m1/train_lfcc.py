import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier
)

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)

# Load LFCC features
data = np.load("lfcc_features.npz")

X = data["X"]
y = data["y"]

# Split dataset: 70% training, 15% validation, 15% testing
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp,
    test_size=0.50,
    random_state=42,
    stratify=y_temp
)

print("Training samples:", len(y_train))
print("Validation samples:", len(y_val))
print("Testing samples:", len(y_test))

# Define classifiers
models = {

    "LFCC_SVM": make_pipeline(
        StandardScaler(),
        SVC(
            kernel="rbf",
            C=10,
            gamma="scale",
            probability=True,
            random_state=42
        )
    ),

    "LFCC_RandomForest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=2
    ),

    "LFCC_GradientBoosting": HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.1,
        random_state=42
    )
}

best_model = None
best_name = None
best_f1 = -1

# Train and compare models
for name, model in models.items():

    print(f"\n===== TRAINING {name} =====")

    model.fit(X_train, y_train)

    pred = model.predict(X_val)

    accuracy = accuracy_score(y_val, pred)
    f1 = f1_score(y_val, pred)

    print(f"Validation Accuracy: {accuracy:.2%}")
    print(f"Validation F1: {f1:.2%}")

    joblib.dump(model, f"{name}.pkl")

    if f1 > best_f1:

        best_f1 = f1
        best_model = model
        best_name = name

# Test the selected model
print("\n===== BEST MODEL =====")
print(best_name)

pred = best_model.predict(X_test)

print("\n===== TEST RESULTS =====")

print(
    f"Accuracy: {accuracy_score(y_test, pred):.2%}"
)

print(
    classification_report(
        y_test,
        pred,
        target_names=["Real", "Fake"],
        digits=4
    )
)

print("Confusion Matrix:")
print(confusion_matrix(y_test, pred))

# Save best model
joblib.dump(
    best_model,
    "best_lfcc_model.pkl"
)

print("\nBest LFCC model saved successfully.")