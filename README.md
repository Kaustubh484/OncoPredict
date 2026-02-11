# OncoPredict: Clinical Trial Completion Prediction

Machine learning system predicting clinical trial outcomes with **83.15% accuracy** by integrating data from ClinicalTrials.gov and FDA APIs.


## Problem Statement

**40% of clinical trials terminate early**, wasting over **$800 million annually**. Can we predict which trials are at risk?

## Implemented Solution

Built an end-to-end ML pipeline analyzing **10,000 cancer trials** from ClinicalTrials.gov, enriched with FDA drug approval data, achieving **83% accuracy** in predicting trial completion.

**Key Finding:** Trials with **500+ participants** show **2.3x higher completion rates**.



## Results

| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| **XGBoost** | **83.15%** | 90.01% | 88.43% | 0.89 |
| Random Forest | 83.00% | 90.01% | 87.98% | 0.89 |
| Logistic Regression | 79.50% | 91.14% | 83.32% | 0.87 |

**Top Predictor:** Enrollment size (45% feature importance)



## End-to-End Pipeline

**[View Interactive Flowchart](https://kaustubh484.github.io/OncoPredict/notebooks/OncoPredict_Flowchart_Interactive.html)**

### Data Sources
- **ClinicalTrials.gov API:** 10,000 cancer trials (2000-2025)
- **FDA Drugs@FDA API:** Approved drug database for feature enrichment

### Workflow
1. **Data Collection** - Multi-source API integration
2. **Data Cleaning** - Missing value imputation, outlier capping (99th percentile)
3. **Feature Engineering** - 11 features including enrollment metrics, trial complexity, FDA approval status
4. **Model Training** - Logistic Regression, Random Forest, XGBoost
5. **Evaluation** - Stratified 80/20 split, cross-validation
6. **Deployment** - Interactive Power BI dashboard



## Interactive Dashboard

Explore the complete analysis through our Power BI dashboard:

[![Dashboard Preview](dashboard/screenshots/Executive_Summary.png)](dashboard/)

**Dashboard includes:**
- Executive summary with model performance
- Detailed metrics and confusion matrices
- EDA insights and feature importance
- Actionable recommendations

**[Download Dashboard (.pbix)](dashboard/Dashboard.pbix)** | **[View PDF](dashboard/Dashboard.pdf)** | **[More Screenshots](dashboard/screenshots/)**

## Quick Start

### View Analysis
- **Dashboard:** Download `dashboard/OncoPredict_Dashboard.pbix` (requires Power BI Desktop)
- **Notebooks:** Run `notebooks/01_EDA_and_Data_Cleaning.ipynb` and `notebooks/02_Model_Training.ipynb`
- **Scripts:** See `src/` for data collection, processing, and training code

### Run Locally
```bash
git clone https://github.com/yourusername/OncoPredict.git
cd OncoPredict
pip install -r requirements.txt
jupyter notebook notebooks/
```



## Methodology

**Data Collection:** Integrated 10,000 trials from ClinicalTrials.gov API with FDA-approved drug data

**Data Processing:** Handled missing values (phase: 37.7%, enrollment: 1.9%), capped outliers at 99th percentile

**Feature Engineering:** Created 11 features including enrollment_log (45% importance), trial_complexity, tests_approved_drug (FDA integration)

**Model Training:** Compared 3 algorithms with stratified cross-validation on 8,000 training trials

**Evaluation:** Tested on 2,000 holdout trials, achieving 83.15% accuracy with XGBoost



## Business Impact

- **Pharmaceutical Companies:** Identify 83% of at-risk trials early, optimize recruitment strategies
- **Trial Managers:** Data-driven enrollment targets (500+ participants = 2.3x success rate)
- **Investors:** Portfolio risk assessment with data-backed predictions



## Technologies

**Data:** ClinicalTrials.gov API, FDA Drugs@FDA API  
**ML:** Python, Scikit-learn, XGBoost, Pandas, NumPy  
**Visualization:** Power BI, Matplotlib, Plotly  

## Author

**Kaustubh Shah**  
[LinkedIn](https://www.linkedin.com/in/kaustubh-shah/) | [Email](kshah115@umd.edu)


