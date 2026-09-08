# Bronze Tier Processing Pipeline (NPT Manuscript ETL)

This document details the architecture, inputs, execution commands, regex patterns, and deterministic vs. probabilistic rules governing the **Bronze Manuscript Processing Stage**.

---

## 1. Pipeline Overview & Input Sources

The **Bronze Tier** represents the raw, unedited, first-stage extraction of the manuscript into individual chapter files and localized reference lists.

### Primary Input Files & Locations:
* **GCS Monolith Source**: `gs://npt-ship/manuscript/bronze/2026-02-24AChapters_complete.md`
* **Local Fallback Source**: `./manuscript/2026-02-24AChapters_complete.md` (374 KB raw markdown monolith containing all 12 chapters plus Introduction & Conclusion).

---

## 2. Managing Agent & Code Controllers

* **Managing Agent**: **BILGELADLE** (Thesis Alignment Engine and Master Philologist).
* **Code Controller Module**: [`src/react_agent/tools/manuscript_etl.py`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/tools/manuscript_etl.py)
* **Primary Python Function**: `process_bronze_manuscript(bronze_gcs_path, target_chapter)`

---

## 3. Invocation Commands

### A. Run via Command Line (Powershell / Shell)
To execute the full Bronze extraction across all chapters:
```bash
python -c "import sys, os; sys.path.append('src'); from dotenv import load_dotenv; load_dotenv(); from react_agent.tools.manuscript_etl import process_bronze_manuscript; print(process_bronze_manuscript())"
```

To target a single chapter (e.g., Chapter 1):
```bash
python -c "import sys, os; sys.path.append('src'); from dotenv import load_dotenv; load_dotenv(); from react_agent.tools.manuscript_etl import process_bronze_manuscript; print(process_bronze_manuscript(target_chapter=1))"
```

### B. Run via Bilgeladle Terminal Session
Inside `python src/react_agent/entrypoints/bilgeladle_runner.py`:
```text
[AUTHOR] -> process_bronze_manuscript()
```

---

## 4. Code Snippets: Exact Regex & Output Destinations

### Regex Pattern 1: Chapter Boundary Slicing
Normalizes heading levels and identifies chapter start boundaries:
```python
# Header normalization
normalized_text = re.sub(r'^[ \t]*([#]+)[ \t]*', r'\1 ', raw_text, flags=re.MULTILINE)

# Chapter boundary regex
chapter_regex = re.compile(
    r'^(#+\s*(?:\*\*|\*)*\s*(?:Chapter\s+\d+|Introduction|Conclusion).*?)(?=(?:^#+\s*(?:\*\*|\*)*\s*(?:Chapter\s+\d+|Introduction|Conclusion)|\Z))',
    re.MULTILINE | re.DOTALL | re.IGNORECASE
)
```

### Regex Pattern 2: Reference List Slicing
Splits body prose from the chapter's tail reference section:
```python
works_cited_match = re.search(
    r'^(#+\s+(?:Master\s+Index\s+of\s+Artifacts|Master\s+List\s+of\s+Artifacts|Works\s+Cited|Bibliography|References).*)$',
    ch_raw_text, re.IGNORECASE | re.MULTILINE | re.DOTALL
)
```

### Output File Paths:
For each extracted Chapter $N$:
1. **Google Cloud Storage Bucket**:
   * `gs://npt-ship/manuscript/bronze/chapter_{N}.md` *(Raw Body Prose)*
   * `gs://npt-ship/manuscript/bronze/chapter_{N}_references.md` *(Raw Reference List)*
2. **Local Workstation Cache**:
   * `./manuscript/bronze/chapter_{N}.md`
   * `./manuscript/bronze/chapter_{N}_references.md`

---

## 5. Deterministic vs. Probabilistic Determinations

| Determination Type | Processing Actions | Guarantees / Behavior |
| :--- | :--- | :--- |
| **DETERMINISTIC (100% Code-Driven)** | • File streaming from GCS / Local fallback.<br>• Regex-based heading normalization.<br>• Boundary slicing of Chapter $N$ body prose.<br>• Boundary slicing of `# Master Index of Artifacts` reference text.<br>• Byte writing & blob creation to local disk and GCS `gs://npt-ship/manuscript/bronze/`. | 100% deterministic Python regex execution. Zero LLM calls are made during the Bronze step. The output is a strict, bit-accurate structural slice of the monolith. |
| **PROBABILISTIC (0% in Bronze)** | • None. | No probabilistic model predictions, vector embeddings, or generative calls occur during Bronze extraction. (Probabilistic operations are strictly deferred to Silver inline citation resolution and section expansions). |
