from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Set project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.ingestion import ingest


def main() -> None:
    sample_dir = ROOT / "data" / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(sample_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No pdfs found in {sample_dir}. Drop some .pdf here")
        return

    print(f"Ingesting {len(pdfs)} pdfs..")

    tenant_id = os.environ.get("SAMPLE_TENANT_ID")
    n = ingest([str(p) for p in pdfs], tenant_id=tenant_id)

    print(f"Done: {n} chunks indexed for tenant={tenant_id}")


if __name__ == "__main__":
    main()