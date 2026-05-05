import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv
import os

def check_golden_dataset():
    qa_path = Path(__file__).parent/ "golden_set" / "qa.jsonl"
    
    
    if not qa_path.exists():
        print(f" Golden set not found:{qa_path}")
        print(f" Create it with: touch {qa_path}")
        return False
    
    with open(qa_path) as f:
        lines = [l for l in f if l.strip()]
        
    
    if not lines:
        print(f"Golden set is empty")
        return False
    
    print(f" golden set: {len(lines)} questions")
    return True


def check_api():
    
    api_url = os.getenv("API_BASE_URL","http://127.0.0.1:5555")
    
    
    
    try:
        response = httpx.get(f"{api_url}/docs", timeout=40.0)
        print(f"Api running {response}")
        return True
    except Exception as e:
        print(f"API Not accessible at {api_url}")
        return False
        
        
def check_dependencies():
    required = ["ragas","datasets","langchain","httpx","pandas"] 
    missing =[]
    
    for pkg in required:
        try:
            __import__(pkg.replace("-","_"))
            
        except ImportError:
            missing.append(pkg)     
            
        if missing:
            print(f" missing - {','.join(missing)}")
            return False

def main():
    print("="*60)
    print("Ragas Evaluation Pre_flight checj")
    print("="*60+"\n")
    
    checks = [
        ("Dependedncies", check_dependencies),
        ("API", check_api),
        ("Golden Set", check_golden_dataset),
        
    ]
    
    results =[]
    
    for name, check_fn in checks:
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            results.append((name, False))
        print()
        
        
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    
    if passed ==total:
        print("All check passed")
    
    
    print("="*60)
    
    
if __name__ == "__main__":
    main()