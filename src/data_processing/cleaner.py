"""
Clinical Trials Data Cleaner
Processes raw JSON from ClinicalTrials.gov into clean pandas DataFrame
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class TrialDataCleaner:
    """Clean and structure clinical trial data"""
    
    def __init__(self):
        self.raw_dir = Path("../../data/raw/clinicaltrials")
        self.processed_dir = Path("../../data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def load_raw_data(self, filepath: str) -> List[Dict]:
        """Load raw JSON data"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            print(f"  Format: Dictionary with {len(data)} trials (converting to list)")
            data = list(data.values())
        elif isinstance(data, list):
            print(f"  Format: List with {len(data)} trials")
        
        return data
    
    def extract_trial_info(self, trial: Dict) -> Dict:
        """
        Extract key information from a single trial
        
        Returns flat dictionary suitable for DataFrame row
        """
        protocol = trial.get("protocolSection", {})
        
        # Identification
        identification = protocol.get("identificationModule", {})
        nct_id = identification.get("nctId", "")
        title = identification.get("briefTitle", "")
        official_title = identification.get("officialTitle", "")
        
        # Status
        status = protocol.get("statusModule", {})
        overall_status = status.get("overallStatus", "")
        start_date = status.get("startDateStruct", {}).get("date", "")
        completion_date = status.get("completionDateStruct", {}).get("date", "")
        
        # Design
        design = protocol.get("designModule", {})
        
        # Enrollment (from designModule, not statusModule!)
        enrollment_info = design.get("enrollmentInfo", {})
        enrollment_count = enrollment_info.get("count", np.nan)
        enrollment_type = enrollment_info.get("type", "")
        
        # Sponsor
        sponsor = protocol.get("sponsorCollaboratorsModule", {})
        lead_sponsor = sponsor.get("leadSponsor", {}).get("name", "")
        sponsor_class = sponsor.get("leadSponsor", {}).get("class", "")
        
        # Phase and study design (from designModule)
        phases = design.get("phases", [])
        phase = phases[0] if phases else ""
        study_type = design.get("studyType", "")
        
        # Allocation and masking
        allocation = design.get("designInfo", {}).get("allocation", "")
        intervention_model = design.get("designInfo", {}).get("interventionModel", "")
        masking = design.get("designInfo", {}).get("maskingInfo", {}).get("masking", "")
        
        # Interventions
        interventions = protocol.get("armsInterventionsModule", {}).get("interventions", [])
        intervention_types = [i.get("type", "") for i in interventions]
        intervention_names = [i.get("name", "") for i in interventions]
        
        # Conditions
        conditions = protocol.get("conditionsModule", {}).get("conditions", [])
        
        # Outcomes
        outcomes = protocol.get("outcomesModule", {})
        primary_outcomes = outcomes.get("primaryOutcomes", [])
        primary_outcome_measures = [o.get("measure", "") for o in primary_outcomes]
        
        # Eligibility
        eligibility = protocol.get("eligibilityModule", {})
        min_age = eligibility.get("minimumAge", "")
        max_age = eligibility.get("maximumAge", "")
        sex = eligibility.get("sex", "")
        
        # Results
        has_results = "resultsSection" in trial
        
        return {
            "nct_id": nct_id,
            "title": title,
            "official_title": official_title,
            "overall_status": overall_status,
            "phase": phase,
            "study_type": study_type,
            "enrollment_count": enrollment_count,
            "enrollment_type": enrollment_type,
            "start_date": start_date,
            "completion_date": completion_date,
            "lead_sponsor": lead_sponsor,
            "sponsor_class": sponsor_class,
            "allocation": allocation,
            "intervention_model": intervention_model,
            "masking": masking,
            "intervention_types": ", ".join(intervention_types),
            "intervention_names": ", ".join(intervention_names),
            "conditions": ", ".join(conditions),
            "primary_outcome_measures": ", ".join(primary_outcome_measures),
            "min_age": min_age,
            "max_age": max_age,
            "sex": sex,
            "has_results": has_results
        }
    
    def clean_trials(self, trials: List[Dict]) -> pd.DataFrame:
        """
        Convert list of trials to clean DataFrame
        
        Args:
            trials: List of trial dictionaries from API
        
        Returns:
            Cleaned pandas DataFrame
        """
        print(f"Cleaning {len(trials)} trials...")
        
        # Extract info from each trial
        rows = []
        errors = 0
        
        for i, trial in enumerate(trials):
            try:
                row = self.extract_trial_info(trial)
                rows.append(row)
            except Exception as e:
                errors += 1
                if errors <= 5:  # Show first 5 errors
                    print(f"  Error processing trial {i}: {e}")
        
        print(f"  Successfully processed: {len(rows)}")
        print(f"  Errors: {errors}")
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Data type conversions
        df['enrollment_count'] = pd.to_numeric(df['enrollment_count'], errors='coerce')
        df['has_results'] = df['has_results'].astype(bool)
        
        # Date parsing (handle various formats)
        for date_col in ['start_date', 'completion_date']:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', format='mixed')
        
        print(f"\n✅ Created DataFrame with shape: {df.shape}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Rows: {df.shape[0]}")
        
        return df
    
    def add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add calculated features
        
        Args:
            df: Cleaned trials DataFrame
        
        Returns:
            DataFrame with added features
        """
        print("\nAdding derived features...")
        
        # Trial duration (days)
        df['trial_duration_days'] = (
            df['completion_date'] - df['start_date']
        ).dt.days
        
        # Is trial completed?
        df['is_completed'] = df['overall_status'].isin([
            'COMPLETED', 'TERMINATED', 'WITHDRAWN'
        ])
        
        # Is trial recruiting?
        df['is_recruiting'] = df['overall_status'].isin([
            'RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION'
        ])
        
        # Phase numeric (for sorting/analysis)
        phase_map = {
            'EARLY_PHASE1': 0.5,
            'PHASE1': 1,
            'PHASE2': 2,
            'PHASE3': 3,
            'PHASE4': 4,
            'NA': np.nan
        }
        df['phase_numeric'] = df['phase'].map(phase_map)
        
        # Is randomized?
        df['is_randomized'] = df['allocation'] == 'RANDOMIZED'
        
        # Is blinded?
        df['is_blinded'] = df['masking'].isin(['DOUBLE', 'TRIPLE', 'QUADRUPLE'])
        
        # Sponsor type
        df['is_industry_sponsored'] = df['sponsor_class'] == 'INDUSTRY'
        
        # Count interventions
        df['intervention_count'] = df['intervention_types'].str.split(',').str.len()
        df.loc[df['intervention_types'] == '', 'intervention_count'] = 0
        
        print(f"✅ Added {7} derived features")
        
        return df
    
    def get_data_quality_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate data quality report"""
        
        print("\n" + "="*60)
        print("DATA QUALITY REPORT")
        print("="*60)
        
        # Missing values
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(1)
        
        quality_df = pd.DataFrame({
            'Missing Count': missing,
            'Missing %': missing_pct
        })
        
        quality_df = quality_df[quality_df['Missing Count'] > 0].sort_values(
            'Missing %', ascending=False
        )
        
        print("\nMissing Values:")
        print(quality_df.to_string())
        
        # Phase distribution
        print("\nPhase Distribution:")
        print(df['phase'].value_counts().to_string())
        
        # Status distribution
        print("\nStatus Distribution:")
        print(df['overall_status'].value_counts().to_string())
        
        # Enrollment stats
        print("\nEnrollment Statistics:")
        print(df['enrollment_count'].describe().to_string())
        
        return quality_df
    
    def save_cleaned_data(self, df: pd.DataFrame, filename: str = None):
        """Save cleaned DataFrame"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trials_clean_{timestamp}.csv"
        
        filepath = self.processed_dir / filename
        df.to_csv(filepath, index=False)
        
        file_size_mb = filepath.stat().st_size / (1024 * 1024)
        
        print(f"\nSaved cleaned data to: {filepath}")
        print(f"   File size: {file_size_mb:.2f} MB")
        print(f"   Shape: {df.shape}")


def main():
    """Example usage"""
    cleaner = TrialDataCleaner()
    
    # Load most recent file - supports both immunotherapy and all-cancer datasets
    immuno_files = list(cleaner.raw_dir.glob("immunotherapy_trials_combined_*.json"))
    cancer_files = list(cleaner.raw_dir.glob("all_cancer_trials_*.json"))
    
    # Combine both types and find most recent
    raw_files = immuno_files + cancer_files
    
   # Show available files
    if len(raw_files) > 1:
        print(f"\nFound {len(raw_files)} data files:")
        for f in sorted(raw_files, key=lambda p: p.stat().st_mtime, reverse=True):
            size_mb = f.stat().st_size / (1024*1024)
            print(f"  - {f.name} ({size_mb:.1f} MB)")
        print(f"\nProcessing most recent: ")
    
    latest_file = max(raw_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading: {latest_file.name}")
    
    # Load and clean
    raw_trials = cleaner.load_raw_data(latest_file)
    df = cleaner.clean_trials(raw_trials)
    
    # Add features
    df = cleaner.add_derived_features(df)
    
    # Quality report
    cleaner.get_data_quality_report(df)
    
    # Save
    cleaner.save_cleaned_data(df)


if __name__ == "__main__":
    main()