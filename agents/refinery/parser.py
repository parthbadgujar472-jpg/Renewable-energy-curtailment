"""
PDF Extraction & Normalization Agent (Agent 2 - Refinery)
Extracts structured data from PDFs/Excel/HTML and normalizes schema.
"""

import os
import pandas as pd

class ReportRefineryAgent:
    def __init__(self):
        pass
        
    def process_raw_manifest(self, manifest):
        print(f"[Refinery Agent] Processing raw document from {manifest.get('portal', 'Unknown')}")
        # Formats: searchable_pdf, scanned_pdf, html_table, excel
        format_type = manifest.get('format_type', 'html_table')
        
        # Schema normalization step
        normalized_row = {
            "source_document_id": manifest.get("file_hash", "DOC-000"),
            "region": manifest.get("portal", "SRLDC"),
            "format_type": format_type,
            "pipeline_status": "normalized"
        }
        return normalized_row

if __name__ == "__main__":
    refinery = ReportRefineryAgent()
    res = refinery.process_raw_manifest({"portal": "SRLDC", "format_type": "searchable_pdf"})
    print(res)
