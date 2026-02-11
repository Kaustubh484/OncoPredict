import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def create_completion_labels(trials_df):
    """
    Create binary labels: Will trial complete or terminate?
    
    Args:
        trials_df: DataFrame of clinical trials
    
    Returns:
        DataFrame with 'completed' column (1 = completed, 0 = terminated)
    """
    
  # Define success and failure statuses
    completed_statuses = [
        'COMPLETED',
        'ACTIVE_NOT_RECRUITING'  # Finished enrollment, in follow-up → likely to complete
    ]
    failed_statuses = ['TERMINATED', 'WITHDRAWN', 'SUSPENDED']
    ongoing_statuses = ['RECRUITING', 'NOT_YET_RECRUITING', 
                       'ENROLLING_BY_INVITATION', 'UNKNOWN']
    
    print(f"\nTotal trials in dataset: {len(trials_df):,}")
    
    # Show status breakdown
    print("\nStatus breakdown:")
    status_counts = trials_df['overall_status'].value_counts()
    for status, count in status_counts.head(10).items():
        print(f"  {status}: {count:,}")
    
    # Filter to trials with clear outcomes
    has_outcome = trials_df['overall_status'].isin(completed_statuses + failed_statuses)
    ml_df = trials_df[has_outcome].copy()
    
  
    
    # Create binary label
    ml_df['completed'] = ml_df['overall_status'].isin(completed_statuses).astype(int)
    
    # Statistics
    print(f"\nTotal examples: {len(ml_df):,}")
    print(f"  Completed (Label=1): {(ml_df['completed'] == 1).sum():,} ({(ml_df['completed'] == 1).sum()/len(ml_df)*100:.1f}%)")
    print(f"  Terminated (Label=0): {(ml_df['completed'] == 0).sum():,} ({(ml_df['completed'] == 0).sum()/len(ml_df)*100:.1f}%)")
    
    # By phase
    print("\nCompletion rate by phase:")
    phase_stats = ml_df.groupby('phase')['completed'].agg(['count', 'mean'])
    phase_stats = phase_stats.sort_values('count', ascending=False)
    for phase, row in phase_stats.iterrows():
        if row['count'] > 10:  # Only show phases with >10 trials
            print(f"  {phase:15s}: {int(row['count']):4d} trials, {row['mean']*100:5.1f}% complete")
    
    # By sponsor type
    print("\nCompletion rate by sponsor type:")
    sponsor_stats = ml_df.groupby('sponsor_class')['completed'].agg(['count', 'mean'])
    sponsor_stats = sponsor_stats.sort_values('count', ascending=False)
    for sponsor, row in sponsor_stats.iterrows():
        if row['count'] > 10:
            print(f"  {sponsor:15s}: {int(row['count']):4d} trials, {row['mean']*100:5.1f}% complete")
    
    # By randomization
    if 'is_randomized' in ml_df.columns:
        print("\nCompletion rate by randomization:")
        rand_stats = ml_df.groupby('is_randomized')['completed'].agg(['count', 'mean'])
        for is_rand, row in rand_stats.iterrows():
            rand_label = "Randomized" if is_rand else "Non-randomized"
            print(f"  {rand_label:15s}: {int(row['count']):4d} trials, {row['mean']*100:5.1f}% complete")
    
    # By enrollment size
    if 'enrollment_count' in ml_df.columns:
        print("\nCompletion rate by enrollment size:")
        ml_df['enrollment_bucket'] = pd.cut(
            ml_df['enrollment_count'], 
            bins=[0, 30, 100, 300, 10000],
            labels=['Small (<30)', 'Medium (30-100)', 'Large (100-300)', 'Very Large (300+)']
        )
        enroll_stats = ml_df.groupby('enrollment_bucket')['completed'].agg(['count', 'mean'])
        for bucket, row in enroll_stats.iterrows():
            if row['count'] > 10:
                print(f"  {bucket:20s}: {int(row['count']):4d} trials, {row['mean']*100:5.1f}% complete")
    
    return ml_df


def add_optional_fda_feature(ml_df, fda_file=None):
    
    if fda_file is None:
        fda_dir = Path("../../data/raw/fda")
        
        # Look for all FDA drug files (immunotherapy, all_cancer, manual)
      
        manual_files = list(fda_dir.glob("all_cancer_drugs_manual_*.json"))
        
        fda_files =  manual_files
        
        if not fda_files:
            print("\nNo FDA data found - skipping FDA feature")
            return ml_df
        
        # Use the most recent file
        fda_file = max(fda_files, key=lambda p: p.stat().st_mtime)
        print(f"\nUsing FDA drug file: {fda_file.name}")
    
    import json
    with open(fda_file, 'r') as f:
        fda_data = json.load(f)
    
    approved_drugs = list(fda_data.keys())
    print(f"\nFDA-approved drugs in database: {len(approved_drugs)}")
    print(f"  {', '.join(approved_drugs[:5])}...")
    
    # Extract drug names from trials
    def has_approved_drug(intervention_names):
        if pd.isna(intervention_names):
            return 0
        
        intervention_names = str(intervention_names).lower()
        
        for drug in approved_drugs:
            if drug.lower() in intervention_names:
                return 1
        
        return 0
    
    ml_df['tests_approved_drug'] = ml_df['intervention_names'].apply(has_approved_drug)
    
    # Statistics
    print(f"\nTrials testing FDA-approved drugs: {ml_df['tests_approved_drug'].sum():,} ({ml_df['tests_approved_drug'].sum()/len(ml_df)*100:.1f}%)")
    
    # Does it correlate with completion?
    if ml_df['tests_approved_drug'].sum() > 10:
        approved_completion = ml_df[ml_df['tests_approved_drug'] == 1]['completed'].mean()
        other_completion = ml_df[ml_df['tests_approved_drug'] == 0]['completed'].mean()
        
        print(f"Completion rates:")
        print(f"  Testing approved drug: {approved_completion*100:.1f}%")
        print(f"  Testing other drugs: {other_completion*100:.1f}%")
        print(f"  Difference: {(approved_completion - other_completion)*100:+.1f} percentage points")
    
    return ml_df


def main():
    """Create ML-ready dataset for trial completion prediction"""
    
    # Load cleaned trials
    processed_dir = Path("../../data/processed")
    trial_files = list(processed_dir.glob("trials_clean_*.csv"))
    
    if not trial_files:
        print("No cleaned trial data found")
        print("Run: python cleaner.py")
        return
    
    latest_file = max(trial_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading trials from: {latest_file.name}")
    
    trials_df = pd.read_csv(latest_file, parse_dates=['start_date', 'completion_date'])
    print(f"Loaded {len(trials_df):,} trials")
    
    # Create completion labels
    ml_df = create_completion_labels(trials_df)
    
    # Add optional FDA feature
    ml_df = add_optional_fda_feature(ml_df)
    
    # Save
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = processed_dir / f"trials_completion_ml_{timestamp}.csv"
    ml_df.to_csv(output_file, index=False)
    print(f"\nFile: {output_file.name}")
    print(f"   Size: {output_file.stat().st_size / (1024*1024):.2f} MB")
    print(f"   Rows: {len(ml_df):,}")
    print(f"   Columns: {ml_df.shape[1]}")
    
  
    if __name__ == "__main__":
     main()
