
import requests
import json
from pathlib import Path
from datetime import datetime
import time

def collect_all_cancer_trials(max_trials=10000, trials_per_request=100):
    """
    Collect cancer trials from ClinicalTrials.gov
    
    Args:
        max_trials: Maximum number of trials to collect (default: 10,000)
        trials_per_request: Trials per API request (max: 1000)
    
    Returns:
        dict: Collected trials data
    """
    
    print("="*70)
    print("COLLECTING ALL CANCER TRIALS - EXPANDED DATASET")
    print("="*70)
    print(f"\nTarget: {max_trials:,} trials")
    print(f"This will significantly increase your sample size!")
    
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # Search for all cancer-related trials
    search_params = {
        'query.cond': 'cancer OR neoplasm OR carcinoma OR tumor OR malignancy',
        'filter.overallStatus': 'COMPLETED,TERMINATED,WITHDRAWN,SUSPENDED,ACTIVE_NOT_RECRUITING',
        'pageSize': min(trials_per_request, 1000),
        'format': 'json',
        'fields': 'NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,EnrollmentCount,EnrollmentType,StartDate,CompletionDate,StudyType,DesignAllocation,DesignInterventionModel,DesignMasking,DesignPrimaryPurpose,LeadSponsorName,LeadSponsorClass,InterventionType,InterventionName,Condition,BriefSummary,HasResults'
    }
    
    all_trials = {}
    page_token = None
    total_collected = 0
    
    print(f"   Search: Cancer-related trials with outcomes")
    print(f"   Page size: {search_params['pageSize']}")
    
    while total_collected < max_trials:
        try:
            # Add page token if continuing
            if page_token:
                search_params['pageToken'] = page_token
            
            # Make request
            response = requests.get(base_url, params=search_params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract trials
            if 'studies' in data:
                batch_trials = data['studies']
                
                for trial in batch_trials:
                    nct_id = trial.get('protocolSection', {}).get('identificationModule', {}).get('nctId')
                    
                    if nct_id:
                        all_trials[nct_id] = trial
                        total_collected += 1
                        
                        if total_collected >= max_trials:
                            break
                
                print(f"   Collected: {total_collected:,} trials...", end='\r')
            
            # Check if more pages available
            if 'nextPageToken' in data and total_collected < max_trials:
                page_token = data['nextPageToken']
                time.sleep(0.5)  # Rate limiting
            else:
                break
                
        except requests.exceptions.RequestException as e:
            
            print("Retrying in 5 seconds...")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"\nError: {e}")
            break
    
    
    print(f"   Total trials collected: {len(all_trials):,}")
    
    return all_trials


def save_trials(trials_data, output_dir="../../data/raw/clinicaltrials"):
    """Save collected trials to JSON file"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"all_cancer_trials_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w') as f:
        json.dump(trials_data, f, indent=2)
    
    file_size_mb = filepath.stat().st_size / (1024 * 1024)
    
    print(f"\nSaved to: {filename}")
    print(f"   Size: {file_size_mb:.2f} MB")
    print(f"   Trials: {len(trials_data):,}")
    
    return filepath


def main():
    """Main execution"""
    # Collect trials
    trials = collect_all_cancer_trials(max_trials=target_trials)
    
    if trials:
        # Save
        filepath = save_trials(trials)
        
       # Count statuses
        statuses = {}
        phases = {}
        
        for trial in trials.values():
            status = trial.get('protocolSection', {}).get('statusModule', {}).get('overallStatus')
            phase_list = trial.get('protocolSection', {}).get('designModule', {}).get('phases', [])
            phase = phase_list[0] if phase_list else 'N/A'
            
            statuses[status] = statuses.get(status, 0) + 1
            phases[phase] = phases.get(phase, 0) + 1
        
        print(f"\nTop statuses:")
        for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {status:30s}: {count:>6,} ({count/len(trials)*100:>5.1f}%)")
        
        print(f"\nTop phases:")
        for phase, count in sorted(phases.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {phase:30s}: {count:>6,} ({count/len(trials)*100:>5.1f}%)")
        
        # Estimate ML dataset size
        completed_terminated = statuses.get('COMPLETED', 0) + statuses.get('TERMINATED', 0) + \
                              statuses.get('WITHDRAWN', 0) + statuses.get('SUSPENDED', 0) + \
                              statuses.get('ACTIVE_NOT_RECRUITING', 0)
        
    else:
        print("\nNo trials collected")


if __name__ == "__main__":
    main()
