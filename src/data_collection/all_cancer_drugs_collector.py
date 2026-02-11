import requests
import json
from pathlib import Path
from datetime import datetime
import time

def collect_all_cancer_drugs(max_drugs=500):
    """
    Collect ALL FDA-approved cancer drugs from openFDA API
    
    Search terms cover major cancer drug categories:
    - Chemotherapy
    - Targeted therapy
    - Immunotherapy
    - Hormone therapy
    - Biologics
    """
    
    base_url = "https://api.fda.gov/drug/drugsfda.json"
    
    # Search for cancer-related drugs (multiple queries)
    cancer_keywords = [
        "cancer", "carcinoma", "neoplasm", "tumor", "malignancy",
        "leukemia", "lymphoma", "myeloma", "sarcoma", "melanoma",
        "chemotherapy", "antineoplastic", "oncology"
    ]
    
    all_drugs = {}
    
    for keyword in cancer_keywords:
        print(f"\n🔍 Searching for: {keyword}")
        
        try:
            # Build query
            params = {
                'search': f'products.marketing_status:"Prescription" AND (openfda.indication:"{keyword}" OR openfda.pharm_class_epc:"{keyword}")',
                'limit': 100  # Max per request
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'results' in data:
                for result in data['results']:
                    # Extract drug info
                    products = result.get('products', [])
                    openfda = result.get('openfda', {})
                    
                    for product in products:
                        # Get generic name
                        generic_names = openfda.get('generic_name', [])
                        brand_names = openfda.get('brand_name', [])
                        
                        for generic in generic_names:
                            generic_lower = generic.lower().strip()
                            
                            if generic_lower not in all_drugs:
                                all_drugs[generic_lower] = {
                                    'generic_name': generic,
                                    'brand_names': brand_names,
                                    'indication': openfda.get('indication', [''])[0] if openfda.get('indication') else '',
                                    'pharm_class': openfda.get('pharm_class_epc', []),
                                    'approval_date': product.get('marketing_status_date', ''),
                                    'source_keyword': keyword
                                }
                
                print(f"   Found {len(data['results'])} drugs")
            else:
                print(f"   No results")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"   Error: {e}")
            continue
    
    print(f"\nTotal unique drugs collected: {len(all_drugs)}")
    return all_drugs


def add_manual_drugs(drugs_dict):
    """
    Add commonly used cancer drugs that might be missed by API search
    """
    
    manual_drugs = {
        # Classic chemotherapy
        'doxorubicin': {'generic_name': 'Doxorubicin', 'category': 'Chemotherapy'},
        'cisplatin': {'generic_name': 'Cisplatin', 'category': 'Chemotherapy'},
        'paclitaxel': {'generic_name': 'Paclitaxel', 'category': 'Chemotherapy'},
        'carboplatin': {'generic_name': 'Carboplatin', 'category': 'Chemotherapy'},
        'fluorouracil': {'generic_name': 'Fluorouracil', 'category': 'Chemotherapy'},
        '5-fu': {'generic_name': '5-Fluorouracil', 'category': 'Chemotherapy'},
        'gemcitabine': {'generic_name': 'Gemcitabine', 'category': 'Chemotherapy'},
        'docetaxel': {'generic_name': 'Docetaxel', 'category': 'Chemotherapy'},
        'cyclophosphamide': {'generic_name': 'Cyclophosphamide', 'category': 'Chemotherapy'},
        'methotrexate': {'generic_name': 'Methotrexate', 'category': 'Chemotherapy'},
        
        # Targeted therapy
        'imatinib': {'generic_name': 'Imatinib', 'category': 'Targeted therapy'},
        'erlotinib': {'generic_name': 'Erlotinib', 'category': 'Targeted therapy'},
        'gefitinib': {'generic_name': 'Gefitinib', 'category': 'Targeted therapy'},
        'sunitinib': {'generic_name': 'Sunitinib', 'category': 'Targeted therapy'},
        'sorafenib': {'generic_name': 'Sorafenib', 'category': 'Targeted therapy'},
        'vemurafenib': {'generic_name': 'Vemurafenib', 'category': 'Targeted therapy'},
        'dabrafenib': {'generic_name': 'Dabrafenib', 'category': 'Targeted therapy'},
        'trastuzumab': {'generic_name': 'Trastuzumab', 'category': 'Targeted therapy (HER2)'},
        'bevacizumab': {'generic_name': 'Bevacizumab', 'category': 'Targeted therapy (VEGF)'},
        'cetuximab': {'generic_name': 'Cetuximab', 'category': 'Targeted therapy (EGFR)'},
        
        # Hormone therapy
        'tamoxifen': {'generic_name': 'Tamoxifen', 'category': 'Hormone therapy'},
        'letrozole': {'generic_name': 'Letrozole', 'category': 'Hormone therapy'},
        'anastrozole': {'generic_name': 'Anastrozole', 'category': 'Hormone therapy'},
        'exemestane': {'generic_name': 'Exemestane', 'category': 'Hormone therapy'},
        'fulvestrant': {'generic_name': 'Fulvestrant', 'category': 'Hormone therapy'},
        
        # Immunotherapy (ensure we have all)
        'pembrolizumab': {'generic_name': 'Pembrolizumab', 'category': 'Immunotherapy (PD-1)'},
        'nivolumab': {'generic_name': 'Nivolumab', 'category': 'Immunotherapy (PD-1)'},
        'atezolizumab': {'generic_name': 'Atezolizumab', 'category': 'Immunotherapy (PD-L1)'},
        'durvalumab': {'generic_name': 'Durvalumab', 'category': 'Immunotherapy (PD-L1)'},
        'ipilimumab': {'generic_name': 'Ipilimumab', 'category': 'Immunotherapy (CTLA-4)'},
    }
    
    added = 0
    for drug_key, drug_info in manual_drugs.items():
        if drug_key not in drugs_dict:
            drugs_dict[drug_key] = drug_info
            added += 1
    
    
    return drugs_dict


def save_drugs(drugs_data, output_dir="../../data/raw/fda"):
    """Save collected drugs to JSON file"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"all_cancer_drugs_combined_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w') as f:
        json.dump(drugs_data, f, indent=2)
    
    file_size_kb = filepath.stat().st_size / 1024
    
    print(f"\n💾 Saved to: {filename}")
    print(f"   Size: {file_size_kb:.1f} KB")
    print(f"   Drugs: {len(drugs_data):,}")
    return filepath


def main():
    """Main execution"""
    # Collect from FDA API
    drugs = collect_all_cancer_drugs()
    
    # Add manual drugs
    drugs = add_manual_drugs(drugs)
    
    if drugs:
        # Save
        filepath = save_drugs(drugs)
        print(f"\nTotal drugs: {len(drugs)}")
    else:
        print("\nNo drugs collected")


if __name__ == "__main__":
    main()
