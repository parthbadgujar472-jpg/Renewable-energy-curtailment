"""
Portal Scraping & Ingestion Agent (Agent 1 - Scout)
Maintains portal registry and ingests raw curtailment/generation documents.
"""

import os
import hashlib
from datetime import datetime

class PortalScoutAgent:
    def __init__(self, registry_config=None):
        self.registry = registry_config or {
            "SRLDC": {"url": "https://srldc.in/reports/curtailment", "format": "searchable_pdf"},
            "WRLDC": {"url": "https://wrldc.in/reports/daily_re", "format": "html_table"},
            "CEA": {"url": "https://gen-re.cea.gov.in/daily_reports", "format": "excel"}
        }
        
    def poll_and_ingest(self, target_dir="data/raw"):
        os.makedirs(target_dir, exist_ok=True)
        manifests = []
        
        for portal, info in self.registry.items():
            now = datetime.now()
            file_name = f"{portal}_daily_{now.strftime('%Y%m%d')}.csv"
            file_path = os.path.join(target_dir, file_name)
            
            # Simulated file hash & manifest generation
            dummy_content = f"Portal: {portal}, Timestamp: {now.isoformat()}"
            file_hash = hashlib.sha256(dummy_content.encode('utf-8')).hexdigest()
            
            manifest = {
                "source_url": info["url"],
                "portal": portal,
                "report_date": now.strftime("%Y-%m-%d"),
                "format_type": info["format"],
                "file_path": file_path,
                "file_hash": file_hash[:16],
                "downloaded_at": now.isoformat(),
                "status": "raw_ingested"
            }
            manifests.append(manifest)
            
        print(f"[Scout Agent] Polled {len(manifests)} portals successfully.")
        return manifests

if __name__ == "__main__":
    scout = PortalScoutAgent()
    scout.poll_and_ingest()
