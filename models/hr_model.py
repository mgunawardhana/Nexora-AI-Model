import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


class HRPerformanceModel:
    """HR Employee Performance Prediction Model"""

    def __init__(self, model_dir: str = None):
        """Initialize the HR Performance Model

        Args:
            model_dir: Directory to save/load model artifacts
        """
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent / "trained_models"
        self.model_dir.mkdir(exist_ok=True)

        # Model components
        self.model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.class_mapping = {}
        self.reverse_class_mapping = {}
        self.feature_order = []
        self.categorical_cols = []
        self.numerical_cols = []
        self.is_trained = False

        # Model paths
        self.model_path = self.model_dir / "xgb_model.pkl"
        self.encoders_path = self.model_dir / "label_encoders.pkl"
        self.scaler_path = self.model_dir / "scaler.pkl"
        self.metadata_path = self.model_dir / "model_metadata.pkl"

    def load_and_prepare_data(self, csv_path: str) -> pd.DataFrame:
        """Load and prepare the HR dataset"""
        df = pd.read_csv(csv_path)

        # Drop irrelevant columns as in original code
        columns_to_drop = ['EmployeeNumber', 'Attrition', 'EmployeeCount', 'Over18', 'StandardHours',
                           'PercentSalaryHike']
        df = df.drop([col for col in columns_to_drop if col in df.columns], axis=1)

        return df

    def train_model(self, csv_path: str) -> Dict:
        """Train the HR performance prediction model"""
        # Load data
        df = self.load_and_prepare_data(csv_path)

        # Define target and features
        target = 'PerformanceRating'
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found in dataset")

        features = df.columns.drop(target).tolist()
        self.feature_order = features

        # Get class distribution
        original_distribution = df[target].value_counts().to_dict()

        # Identify categorical and numerical columns
        self.categorical_cols = df[features].select_dtypes(include=['object']).columns.tolist()
        self.numerical_cols = df[features].select_dtypes(include=['int64', 'float64']).columns.tolist()

        # Encode categorical features
        df_encoded = df.copy()
        for col in self.categorical_cols:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col])
            self.label_encoders[col] = le

        # Handle class labels
        unique_classes = sorted(df_encoded[target].unique())
        self.class_mapping = {cls: i for i, cls in enumerate(unique_classes)}
        self.reverse_class_mapping = {i: cls for cls, i in self.class_mapping.items()}

        # Apply class mapping
        y = df_encoded[target].map(self.class_mapping)
        X = df_encoded[features]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Scale numerical features
        if self.numerical_cols:
            X_train[self.numerical_cols] = self.scaler.fit_transform(X_train[self.numerical_cols])
            X_test[self.numerical_cols] = self.scaler.transform(X_test[self.numerical_cols])

        # Determine model configuration
        num_classes = len(unique_classes)

        if num_classes == 2:
            # Binary classification
            neg_samples = sum(y_train == 0)
            pos_samples = sum(y_train == 1)
            scale_pos_weight = neg_samples / pos_samples if pos_samples > 0 else 1.0

            self.model = xgb.XGBClassifier(
                objective='binary:logistic',
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
                eval_metric='logloss',
                scale_pos_weight=scale_pos_weight
            )
        else:
            # Multi-class classification
            self.model = xgb.XGBClassifier(
                objective='multi:softmax',
                num_class=num_classes,
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
                eval_metric='mlogloss'
            )

        # Train model
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_original = [self.reverse_class_mapping[pred] for pred in y_pred]
        y_test_original = [self.reverse_class_mapping[test] for test in y_test]

        accuracy = accuracy_score(y_test_original, y_pred_original)

        # Save model
        self.is_trained = True
        self.save_model()

        return {
            "status": "success",
            "message": "Model trained successfully",
            "accuracy": float(accuracy),
            "original_class_distribution": {str(k): int(v) for k, v in original_distribution.items()},
            "mapped_class_distribution": {str(k): int(v) for k, v in y.value_counts().to_dict().items()},
            "num_features": int(len(features)),
            "num_classes": int(num_classes),
            "feature_names": list(features)
        }

    def save_model(self):
        """Save the trained model and associated artifacts"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")

        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)

        # Save label encoders
        with open(self.encoders_path, 'wb') as f:
            pickle.dump(self.label_encoders, f)

        # Save scaler
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save metadata
        metadata = {
            'class_mapping': self.class_mapping,
            'reverse_class_mapping': self.reverse_class_mapping,
            'feature_order': self.feature_order,
            'categorical_cols': self.categorical_cols,
            'numerical_cols': self.numerical_cols,
            'is_trained': self.is_trained
        }
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

    def load_model(self) -> bool:
        """Load the trained model and associated artifacts"""
        try:
            # Check if all required files exist
            required_files = [self.model_path, self.encoders_path, self.scaler_path, self.metadata_path]
            if not all(f.exists() for f in required_files):
                return False

            # Load model
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)

            # Load label encoders
            with open(self.encoders_path, 'rb') as f:
                self.label_encoders = pickle.load(f)

            # Load scaler
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                self.class_mapping = metadata['class_mapping']
                self.reverse_class_mapping = metadata['reverse_class_mapping']
                self.feature_order = metadata['feature_order']
                self.categorical_cols = metadata['categorical_cols']
                self.numerical_cols = metadata['numerical_cols']
                self.is_trained = metadata['is_trained']

            return True

        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def predict_single(self, employee_data: Dict) -> Dict:
        """Predict performance for a single employee"""
        if not self.is_trained and not self.load_model():
            raise ValueError("Model is not trained and cannot be loaded. Please train the model first.")

        try:
            # Create DataFrame from input
            input_df = pd.DataFrame([employee_data])

            # Reorder columns to match training data
            input_df = input_df.reindex(columns=self.feature_order)

            # Check for missing features
            missing_features = [f for f in self.feature_order if f not in employee_data]
            if missing_features:
                return {
                    "status": "error",
                    "message": f"Missing required features: {missing_features}"
                }

            # Encode categorical features
            for col in self.categorical_cols:
                if col in input_df.columns:
                    value = employee_data[col]
                    if value not in self.label_encoders[col].classes_:
                        return {
                            "status": "error",
                            "message": f"Unknown category '{value}' for feature '{col}'"
                        }
                    input_df[col] = self.label_encoders[col].transform([value])[0]

            # Scale numerical features
            if self.numerical_cols:
                input_df[self.numerical_cols] = self.scaler.transform(input_df[self.numerical_cols])

            # Make prediction
            prediction_mapped = self.model.predict(input_df)[0]
            prediction_original = self.reverse_class_mapping[prediction_mapped]

            # Get prediction probability
            prediction_proba = self.model.predict_proba(input_df)[0]
            confidence = max(prediction_proba)

            # Generate suggestions
            suggestions = self._get_suggestions(prediction_original)

            return {
                "status": "success",
                "prediction": {
                    "performance_rating": int(prediction_original),
                    "confidence": float(confidence),
                    "suggestions": suggestions
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Prediction failed: {str(e)}"
            }

    def predict_batch(self, employees_data: List[Dict]) -> Dict:
        """Predict performance for multiple employees"""
        if not self.is_trained and not self.load_model():
            raise ValueError("Model is not trained and cannot be loaded. Please train the model first.")

        results = []
        for i, employee_data in enumerate(employees_data):
            employee_name = employee_data.get('employee_name', f'Employee_{i + 1}')
            prediction_result = self.predict_single(employee_data)
            prediction_result['employee_name'] = employee_name
            results.append(prediction_result)

        return {
            "status": "success",
            "total_employees": int(len(employees_data)),
            "predictions": results
        }

    def _get_suggestions(self, performance_rating: int) -> str:
        """Generate suggestions based on performance rating"""
        suggestions = {
            1: "Critical: Immediate intervention required - performance improvement plan, intensive training, or role reassignment.",
            2: "Below expectations: Suggest mentoring, skill development workshops, and closer supervision.",
            3: "Meets expectations: Encourage continued growth via feedback and development opportunities.",
            4: "Exceeds expectations: Excellent performance - recommend for promotion, leadership roles, or special projects."
        }
        return suggestions.get(performance_rating, "No suggestions available.")

    def get_feature_info(self) -> Dict:
        """Get information about model features"""
        if not self.is_trained and not self.load_model():
            return {"status": "error", "message": "Model not available"}

        return {
            "status": "success",
            "feature_info": {
                "total_features": int(len(self.feature_order)),
                "feature_names": list(self.feature_order),
                "categorical_features": list(self.categorical_cols),
                "numerical_features": list(self.numerical_cols),
                "categorical_feature_values": {
                    col: [str(x) for x in encoder.classes_]
                    for col, encoder in self.label_encoders.items()
                },
                "target_classes": [int(x) for x in self.reverse_class_mapping.values()]
            }
        }

    def get_model_info(self) -> Dict:
        """Get model information and status"""
        model_exists = all(
            f.exists() for f in [self.model_path, self.encoders_path, self.scaler_path, self.metadata_path])

        info = {
            "status": "success",
            "model_info": {
                "is_trained": bool(self.is_trained),
                "model_files_exist": bool(model_exists),
                "model_directory": str(self.model_dir),
                "can_make_predictions": bool(self.is_trained or model_exists)
            }
        }

        if self.is_trained or model_exists:
            if not self.is_trained:
                self.load_model()

            info["model_info"].update({
                "num_features": int(len(self.feature_order)),
                "num_classes": int(len(self.reverse_class_mapping)),
                "target_classes": [int(x) for x in self.reverse_class_mapping.values()]
            })

        return info