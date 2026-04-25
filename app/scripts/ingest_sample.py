from pathlib import Path
from app.services.ingestion import ingest


DATA_DIR = Path(__file__).parent.parent/"data"

def main() -> None:
    pdfs = list(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No pdfs found in{DATA_DIR}. Drop some .pdf here")
        return
    
    total = 0
    for pdf in pdfs:
        print(f"Ingesting{pdf.name} ..")
        count= ingest(pdf)
        print(f" -> {count} chunks")
        total += count
    print(f"\n Done. {total} chunks across {len(pdfs)} PDFs")
    
    
if __name__ == "__main__":
    main()
    
    
    
