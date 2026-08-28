# Abuse Ring Sentinel

Abuse Ring Sentinel is a graph- and entity-based abuse detection system designed to identify coordinated accounts that exhibit shared identity signals and suspicious transaction behavior.

The project combines entity-linkage features, transaction-graph features, behavioral signals, temporal features, and machine learning to produce an account-level abuse probability and an explainable operational risk assessment.

## Problem

Fraudulent or abusive accounts rarely operate independently.

A coordinated abuse ring may reuse:

- Devices
- IP addresses
- Payment instruments
- Addresses
- Multiple identity signals
- Internal transaction relationships

Looking at individual accounts in isolation can therefore miss relationships between apparently unrelated accounts.

Abuse Ring Sentinel models these relationships and converts them into account-level risk assessments.

---

## System Architecture

```text
                         ┌──────────────────────┐
                         │ Synthetic Account    │
                         │ & Transaction Data   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Feature Engineering  │
                         ├──────────────────────┤
                         │ Entity Features      │
                         │ Graph Features       │
                         │ Behavioral Features  │
                         │ Temporal Features    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Leakage Audit        │
                         │ & Feature Analysis   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Machine Learning              │
                    ├───────────────────────────────┤
                    │ Logistic Regression            │
                    │ XGBoost                       │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │ Abuse Probability   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Risk Engine         │
                         ├──────────────────────┤
                         │ Risk Score           │
                         │ Risk Level           │
                         │ Decision              │
                         │ Explainable Reasons   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ FastAPI              │
                         │ Inference Service     │
                         └──────────────────────┘
Feature Engineering

The system uses four major feature groups.

1. Entity Features

Entity features capture relationships between accounts through shared identity or infrastructure signals.

shared_device_count
shared_ip_count
shared_address_count
shared_payment_count
multi_signal_link_count

These features help identify accounts that may be connected through reused infrastructure or identity attributes.

2. Graph Features

Graph features describe the account's position and behavior within the transaction network.

in_degree
out_degree
total_degree
reciprocity
internal_degree

These features help identify accounts involved in dense or reciprocal transaction relationships.

3. Behavioral Features

Behavioral features capture transaction activity.

transaction_count
total_sent
total_received
active_days
transactions_per_active_day

These features describe how frequently and intensely an account interacts with the transaction system.

4. Temporal Features

Temporal features capture the duration of account activity.

activity_span_hours

This provides additional context about the time span over which an account's activity occurs.

Leakage Audit

Before relying on the model results, the feature set was evaluated for feature/label correlation.

Feature / Label Correlation
Feature	Correlation
shared_device_count	0.7037
transaction_count	0.7016
multi_signal_link_count	0.6464
shared_ip_count	0.6363
active_days	0.6337
transactions_per_active_day	0.6229
total_received	0.5760
total_degree	0.5731
total_sent	0.4947
in_degree	0.4769
out_degree	0.4261
reciprocity	0.4043
internal_degree	0.3926
shared_payment_count	0.3547
community_size	0.3085
shared_address_count	0.2652
activity_span_hours	0.2356
average_sent	0.0512
average_received	-0.0280

The strongest individual association is shared_device_count, followed by transaction activity and multi-signal linkage features.

Feature Group ROC-AUC
Feature Group	ROC-AUC
Behavioral only	0.9382
Ring linkage only	0.9804
Full model	0.9930

This shows that the entity/ring-linkage signals provide substantial predictive value, while combining feature groups produces the strongest overall discrimination.

Machine Learning

Two models were evaluated:

Logistic Regression
XGBoost

The Logistic Regression model provides an interpretable baseline, while XGBoost provides a non-linear tree-based comparison.

Model Comparison
Model	Accuracy	Precision	Recall	F1	ROC-AUC
Logistic Regression	0.9700	0.9333	0.8833	0.9048	0.9961
XGBoost	0.9800	1.0000	0.8667	0.9200	0.9843

The Logistic Regression model achieved the stronger ROC-AUC, while XGBoost achieved higher accuracy, precision, and F1 on the evaluated test split.

The project therefore retains Logistic Regression as the inference baseline because it provides strong discrimination while remaining relatively simple and interpretable.

Threshold Analysis

Prediction thresholds were evaluated across multiple probability cutoffs.

Tested thresholds:

0.20
0.25
0.30
0.35
0.40
0.45
0.50
0.55
0.60
0.65
0.70
0.75
0.80

On the evaluated synthetic test set, all tested thresholds produced:

Accuracy  : 1.0000
Precision : 1.0000
Recall    : 1.0000
F1        : 1.0000

The selected threshold was:

0.20

with:

Accuracy  : 1.0000
Precision : 1.0000
Recall    : 1.0000
F1        : 1.0000

These results are specific to the current synthetic dataset and should not be interpreted as expected production performance.

Robustness Evaluation

The model was evaluated beyond the clean test set using synthetic perturbations.

Entity Noise
Noise Level	Accuracy	Precision	Recall	F1	ROC-AUC
0.0	0.97	0.96	0.8833	0.9092	0.9930
0.1	0.97	0.96	0.8833	0.9092	0.9930
0.2	0.95	0.91	0.8333	0.8592	0.9898
0.3	0.95	0.91	0.8333	0.8592	0.9898
0.4	0.96	0.95	0.8333	0.8814	0.9898
0.5	0.96	0.95	0.8333	0.8814	0.9898

The model retains relatively strong ROC-AUC under entity noise, while recall decreases as the perturbation becomes stronger.

Hard Negatives

Hard-negative testing introduces legitimate-looking accounts with characteristics that make them more difficult to distinguish from abusive accounts.

Difficulty	Accuracy	Precision	Recall	F1	ROC-AUC
0.0	0.97	0.9600	0.8833	0.9092	0.9930
0.1	0.98	0.9600	0.9333	0.9378	0.9890
0.2	0.93	0.7867	0.8333	0.8032	0.9718
0.3	0.94	0.8433	0.8333	0.8235	0.9710
0.4	0.93	0.8267	0.8333	0.8121	0.9656
0.5	0.94	0.9143	0.8333	0.8388	0.9640

The results demonstrate that harder negative examples reduce model performance, particularly precision and ROC-AUC.

Combined Noise

Entity noise and hard-negative perturbations were also evaluated together.

Difficulty	Accuracy	Precision	Recall	F1	ROC-AUC
0.0	0.97	0.9600	0.8833	0.9092	0.9930
0.1	0.97	0.9500	0.8833	0.9100	0.9859
0.2	0.92	0.7600	0.8333	0.7854	0.9569
0.3	0.91	0.7976	0.7833	0.7626	0.9593
0.4	0.93	0.8667	0.8333	0.8133	0.9460
0.5	0.94	0.9333	0.7667	0.8133	0.9561

This evaluation demonstrates that the model is reasonably robust under moderate perturbation but that combined noise can materially affect classification performance.

Explainable Risk Engine

The ML model produces an abuse probability.

The risk engine converts this probability into an operational assessment.

Risk Score
risk_score = abuse_probability × 100

The probability is bounded between 0 and 1 before conversion.

Risk Classification
Condition	Risk Level	Decision
Risk score >= 80	CRITICAL	REVIEW
Risk score >= 60	HIGH	REVIEW
Evidence score >= 5	MEDIUM	REVIEW
Risk score >= 30	MEDIUM	MONITOR
Evidence score >= 2	LOW	MONITOR
Otherwise	LOW	ALLOW

This allows the system to combine model probability with observable abuse evidence.

Explainable Evidence

The risk engine does not expose internal model coefficients.

Instead, it generates human-readable reasons from observable account-level signals.

Examples include:

Shared device linked to 4 other accounts
Shared IP linked to 3 other accounts
5 multi-signal account links detected
Payment instrument is shared across multiple accounts
High internal transaction connectivity
High reciprocal transaction activity
Unusually high transaction activity
High transaction frequency relative to active days

The system limits the returned explanation to the strongest available reasons.

Example Risk Assessment

Example output from the inference system:

Abuse Ring Sentinel — Risk Assessment
============================================================

Account           : ACC_00001
Abuse probability : 0.9995
Risk score        : 100/100
Risk level        : CRITICAL
Decision          : REVIEW
Reasons:
  - Shared device linked to 4 other accounts
  - Shared IP linked to 3 other accounts
  - 5 multi-signal account links detected
  - Address is shared across multiple accounts
  - High internal transaction connectivity

A lower-risk example:

Account           : ACC_00048
Abuse probability : 0.0966
Risk score        : 10/100
Risk level        : LOW
Decision          : MONITOR
Reasons:
  - Shared IP linked to 3 other accounts
  - High internal transaction connectivity
Inference Layer

The project includes a dedicated inference module that:

Loads the generated dataset.
Trains the Logistic Regression inference model.
Predicts account-level abuse probability.
Passes the probability and account features to the risk engine.
Returns a structured RiskAssessment.

The assessment contains:

account_id
abuse_probability
risk_score
risk_level
decision
reasons
FastAPI Service

The project exposes the inference system through FastAPI.

Start the API

Activate the virtual environment and run:

uvicorn api.main:app --reload

The API runs by default at:

http://127.0.0.1:8000
API Endpoints
Root
GET /

Returns basic service information.

Example:

{
  "service": "Abuse Ring Sentinel",
  "status": "online",
  "version": "1.0.0"
}
Health Check
GET /health

Example:

{
  "status": "healthy"
}
List Accounts
GET /accounts

Returns account IDs and their dataset labels.

Account Risk
GET /accounts/{account_id}

Example:

GET /accounts/ACC_00001

Returns the account's model probability and operational risk assessment.

Interactive API Documentation

FastAPI automatically provides Swagger documentation at:

http://127.0.0.1:8000/docs

OpenAPI specification is available at:

http://127.0.0.1:8000/openapi.json
API Error Handling

If an account does not exist, the API returns HTTP 404.

Example:

GET /accounts/ACC_99999

Response:

{
  "detail": "Account not found: ACC_99999"
}
Testing

The project contains  covering:

Dataset generation
Feature generation
Risk engine behavior
Model inference
API endpoints
Model-related functionality

Current test result:

111 passed

Run the complete test suite with:

pytest -q

Expected result:

111 passed
Code Quality

The project uses Ruff for Python linting.

Run:

ruff check .

The current codebase passes Ruff checks.

Automatic fixes can be applied with:

ruff check . --fix
Project Structure
abuse-ring-sentinel/
│
├── api/
│   ├── __init__.py
│   └── main.py
│
├── data/
│   ├── __init__.py
│   ├── build_dataset.py
│   ├── generate_accounts.py
│   ├── generate_rings.py
│   └── generate_transactions.py
│
├── features/
│   ├── __init__.py
│   ├── behavioral.py
│   ├── entity_features.py
│   ├── graph_features.py
│   └── temporal.py
│
├── models/
│   ├── __init__.py
│   ├── ablation.py
│   ├── baseline.py
│   ├── inference.py
│   ├── leakage_audit.py
│   ├── model_comparison.py
│   ├── risk_demo.py
│   ├── risk_engine.py
│   ├── robustness.py
│   └── threshold_analysis.py
│
├── tests/
│   ├── test_api.py
│   ├── test_data_generation.py
│   ├── test_inference.py
│   ├── test_model_comparison.py
│   └── test_risk_engine.py
│
├── datasets/
│   └── abuse_ring_dataset.csv
│
├── pyproject.toml
└── README.md
Running the Project
1. Clone the repository
git clone https://github.com/Hridayesh11/abuse-ring-sentinel.git
cd abuse-ring-sentinel
2. Create a virtual environment

Windows:

python -m venv .venv
3. Activate the environment
.venv\Scripts\activate
4. Install dependencies

Install the project's dependencies according to the repository configuration.

5. Run the tests
pytest -q
6. Run model evaluation

Model comparison:

python -m models.model_comparison

Threshold analysis:

python -m models.threshold_analysis

Leakage audit:

python -m models.leakage_audit

Robustness evaluation:

python -m models.robustness
7. Run the risk demonstration
python -m models.risk_demo
8. Start the API
uvicorn api.main:app --reload

Then open:

http://127.0.0.1:8000/docs
Evaluation Summary

The current system demonstrates the following:

Area	Result
Dataset generation	Implemented
Entity features	Implemented
Graph features	Implemented
Behavioral features	Implemented
Temporal features	Implemented
Leakage audit	Implemented
Logistic Regression	Implemented
XGBoost comparison	Implemented
Threshold analysis	Implemented
Robustness testing	Implemented
Explainable risk engine	Implemented
Inference layer	Implemented
FastAPI service	Implemented
Automated tests	111 passing
Ruff linting	Passing
Limitations

This project currently uses a synthetic dataset.

Therefore:

The reported metrics should not be interpreted as production fraud-detection performance.
Synthetic relationships may be cleaner than real-world abuse patterns.
Real-world identity signals can contain missing, noisy, or ambiguous data.
Production deployment would require stronger validation on unseen real-world distributions.
Threshold selection should be based on operational costs such as false positives, false negatives, and review capacity.
Model monitoring and drift detection would be required for a production system.
Future Improvements

Potential next steps include:

Larger and more realistic datasets
Time-based train/test splitting
Cross-validation and out-of-time evaluation
Graph Neural Network experimentation
Model calibration
Precision-recall curve analysis
Automated threshold selection based on review capacity
SHAP-based model interpretation
Feature drift monitoring
Model drift monitoring
Batch scoring pipelines
Persistent model artifacts
Authentication and authorization for the API
Production database integration
Docker containerization
CI/CD pipeline
Production monitoring and alerting
Why This Project Matters

Abuse detection is fundamentally a relationship problem.

A single account may appear normal when viewed independently, but connections through shared devices, IP addresses, payment instruments, addresses, and transaction relationships can reveal coordinated behavior.

Abuse Ring Sentinel demonstrates an end-to-end approach to this problem by combining:

Entity Linkage
      +
Transaction Graph Analysis
      +
Behavioral Analysis
      +
Temporal Signals
      +
Machine Learning
      +
Explainable Risk Scoring
      +
API-based Inference

The result is an account-level abuse detection system that does not stop at a binary prediction. It produces a probability, a risk score, an operational decision, and human-readable evidence explaining why an account was flagged.

Tech Stack
Python
pandas
NumPy
scikit-learn
XGBoost
Network/graph-based feature engineering
FastAPI
Uvicorn
pytest
Ruff
Repository

GitHub:

https://github.com/Hridayesh11/abuse-ring-sentinel

Author

Hridayesh Upadhyay

Computer Science Engineering student specializing in Big Data Analytics.

Built as an end-to-end machine learning and backend engineering project focused on graph-based abuse detection, explainable risk assessment, and production-style API inference.