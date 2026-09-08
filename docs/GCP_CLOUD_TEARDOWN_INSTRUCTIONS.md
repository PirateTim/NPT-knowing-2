# GCP Cloud Teardown Instructions & Idle Cost Analysis

This document provides an exhaustive inventory of all Google Cloud Platform (GCP) resources configured for the **NPT Fleet** in project **`npt-reckoning-1`**, a financial analysis of idle costs over 3 months, and step-by-step teardown, IAM key rotation, and recovery procedures.

---

## 1. Executive Cost Summary: 3-Month Idle Analysis

> **User Question:** *"The DB seems to be the only thing that would incur recurring cost if I left the project idle for 3 months. Correct me if I'm wrong."*

### The Verdict: **You are 100% Correct.**

If you leave this project completely idle for 3 months without deleting anything, **over 98% of your monthly GCP bill will be generated exclusively by Cloud SQL (`npt-instance-postgressql`).**

Here is the exact cost breakdown for 3 months of zero traffic:

| Resource | Service / Name | Configuration | 3-Month Idle Cost |
| :--- | :--- | :--- | :--- |
| **Cloud SQL (Database)** | `npt-instance-postgressql` | `db-f1-micro` + 10GB SSD | **~$36.00 – $45.00** (~$12–$15/mo) |
| **Cloud Run** | `zotero-translator` | Serverless (`--min-instances=0`) | **$0.00** (Scales to zero) |
| **Cloud Build** | Build service | Serverless / Pay-per-build | **$0.00** |
| **Container Registry** | `gcr.io/npt-reckoning-1/zotero-translator` | 305 MB image layer storage | **~$0.09** (~$0.03/mo) |
| **Cloud Storage** | 8 GCS buckets (~1-2 GB total) | Standard Regional Storage | **~$0.15 – $0.30** (~$0.05–$0.10/mo) |
| **IAM Service Accounts & Keys** | 2 custom accounts (7 active keys) | IAM & Admin | **$0.00** (Free, but security vector) |
| **Compute Engine (VMs)** | None active | Listed 0 items | **$0.00** |
| **TOTAL ESTIMATED 3-MONTH COST** | | | **~$36.24 – $45.39** |

---

### The Cloud SQL "7-Day Auto-Restart" Catch
Google Cloud does **not** allow you to permanently "stop" a Cloud SQL instance. If you stop the instance via the console or CLI (`gcloud sql instances patch npt-instance-postgressql --activation-policy=NEVER`), **Google automatically restarts the instance after 7 days** and resumes billing.

Therefore, if you want **true zero cost** during an idle period, you must:
1. Export the database to a `.sql` backup file.
2. Delete the Cloud SQL instance.

---

## 2. Resource & Identity Inventory (`npt-reckoning-1`)

### A. Cloud SQL Instances & Database Users
* **Instance Name**: `npt-instance-postgressql` (PostgreSQL 15, `us-east1-c`, `db-f1-micro`, IP: `34.23.222.39`)
* **Schemas**: `cargo`, `ship`, `agent_state`
* **Database Users**:
  * `postgres`: Default root administrator.
  * `npt_agent_postgressql_admin`: Application user utilized in fleet database connection URLs (`CONTENT_DATABASE_URL`, `DATABASE_URL`).

### B. Cloud Run Services & Public Ingress
* **Service Name**: `zotero-translator` (Region: `us-central1`)
* **Active URL**: `https://zotero-translator-809652732702.us-central1.run.app`
* **Configuration**: `min-instances=0`, `max-instances=2`, `memory=512Mi`, `port=8080`
* **Public Policy**: Configured with `--allow-unauthenticated`. IAM binding `allUsers` has role `roles/run.invoker`.

### C. Container Registry / Artifact Registry
* **Repository**: `gcr.io`
* **Image**: `gcr.io/npt-reckoning-1/zotero-translator:latest` (305 MB)

### D. Cloud Storage Buckets
* `gs://npt-fleet-cargo-hold/`: Primary external cargo hold (`acquisitions/*.txt`).
* `gs://npt-ship/`: Manuscript storage (`ship.letters_of_marque` source).
* `gs://npt-knowing-2-logs/`: Telemetry and turn interaction logs.
* `gs://npt-reckoning-1_cloudbuild/`: Cloud Build cache and staging tarballs.
* `gs://npt-cloud-agents/`: Agent firmware state backups.
* `gs://npt-sources-read/`: Legacy acquisition staging.
* `gs://npt-reckoning-drafts/`: Legacy chapter draft storage.
* `gs://npt-reckoning-scrape-cache/`: Scraper transient cache.

### E. IAM Service Accounts, Roles & Credential Keys

> [!WARNING]
> While IAM service accounts and keys cost **$0.00/month**, active downloaded private JSON keys stored on local development machines represent a persistent security vector if left unmanaged during long periods of dormancy.

1. **`npt-fleet-manager@npt-reckoning-1.iam.gserviceaccount.com`**
   * **Assigned Roles**:
     * `roles/storage.objectAdmin` (Full read/write/delete permissions across all GCS buckets)
     * `roles/bigquery.dataEditor` & `roles/bigquery.jobUser`
     * `roles/aiplatform.user`
     * `roles/cloudsql.admin`
     * `roles/iam.serviceAccountUser`
   * **Active Key IDs**: **4 active private keys** (`859be6be...`, `aa7fdafe...`, `7cfc72d8...`, `51aadd34...`).
2. **`vertex-express@npt-reckoning-1.iam.gserviceaccount.com`**
   * **Assigned Roles**: `roles/aiplatform.expressUser`
   * **Active Key IDs**: **3 active private keys** (`0f3218f8...`, `383ba4bf...`, `1f35c5d6...`).

### F. Cloud Scheduler Automated Start/Stop Jobs (Idle Cost Control)
* **Location**: `us-east1`
* **Monthly Cost**: **$0.00** (Within GCP 3 free jobs/month tier)
* **Active Jobs**:
  1. `start-cloud-sql-morning`: Runs `0 8 * * 1-5` (8:00 AM ET Monday–Friday) $\rightarrow$ PATCH `activationPolicy: ALWAYS`.
  2. `stop-cloud-sql-nightly`: Runs `0 20 * * *` (8:00 PM ET Daily) $\rightarrow$ PATCH `activationPolicy: NEVER`.
* **Cost Impact**: Reduces Cloud SQL idle compute cost to **$0.00** during nights and weekends, reducing idle day costs to **5.6¢ / day**.

---

## 3. Tiered Teardown Instructions

### Option 1: The "Cost-Freeze & Secure Dormancy" Protocol (Recommended)
*Eliminates the Cloud SQL monthly bill and freezes service account keys to prevent unauthorized access, while keeping your data and containers ready for an instant restart.*

#### Step 1: Export Database Dump to GCS
```bash
gcloud sql export sql npt-instance-postgressql gs://npt-fleet-cargo-hold/backups/npt_backup_$(date +%Y%m%d).sql \
    --database=postgres
```

#### Step 2: Delete Cloud SQL Instance
```bash
gcloud sql instances delete npt-instance-postgressql --quiet
```

#### Step 3: Deactivate IAM Service Accounts (Freezes Keys)
Disabling the service accounts immediately revokes the ability of any existing downloaded JSON keys to access GCS or Vertex AI, without deleting the accounts:
```bash
gcloud iam service-accounts disable npt-fleet-manager@npt-reckoning-1.iam.gserviceaccount.com
gcloud iam service-accounts disable vertex-express@npt-reckoning-1.iam.gserviceaccount.com
```

#### Step 4: Remove Public Ingress on Cloud Run (Optional Security Hardening)
Revoke the public `allUsers` invoker permission so external web traffic cannot trigger container cold starts:
```bash
gcloud run services remove-iam-policy-binding zotero-translator \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"
```

---

### How to Re-awaken after a Hiatus (Option 1 Recovery)
When you return to work on the fleet:
```bash
# 1. Re-enable the service accounts (reactivates your existing local keys)
gcloud iam service-accounts enable npt-fleet-manager@npt-reckoning-1.iam.gserviceaccount.com
gcloud iam service-accounts enable vertex-express@npt-reckoning-1.iam.gserviceaccount.com

# 2. Re-create Cloud SQL and restore data
gcloud sql instances create npt-instance-postgressql \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-east1-c

gcloud sql import sql npt-instance-postgressql gs://npt-fleet-cargo-hold/backups/npt_backup_*.sql \
    --database=postgres

# 3. Restore public invoker on Cloud Run (if revoked)
gcloud run services add-iam-policy-binding zotero-translator \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"
```

---

### Option 2: The "Total Wipeout" Protocol (Complete Account Liquidation)
*Destroys every service, container image, storage bucket, database instance, and IAM credential.*

#### Step 1: Delete Cloud Run Service
```bash
gcloud run services delete zotero-translator --region=us-central1 --quiet
```

#### Step 2: Delete Container Images
```bash
gcloud artifacts docker images delete gcr.io/npt-reckoning-1/zotero-translator:latest --delete-tags --quiet
```

#### Step 3: Backup GCS Buckets Locally
```bash
gsutil -m cp -r gs://npt-fleet-cargo-hold/ ./local_gcp_backups/npt-fleet-cargo-hold/
gsutil -m cp -r gs://npt-ship/ ./local_gcp_backups/npt-ship/
```

#### Step 4: Delete All Cloud Storage Buckets
```bash
gsutil rm -r gs://npt-fleet-cargo-hold/
gsutil rm -r gs://npt-ship/
gsutil rm -r gs://npt-knowing-2-logs/
gsutil rm -r gs://npt-cloud-agents/
gsutil rm -r gs://npt-sources-read/
gsutil rm -r gs://npt-reckoning-drafts/
gsutil rm -r gs://npt-reckoning-scrape-cache/
gsutil rm -r gs://npt-reckoning-1_cloudbuild/
```

#### Step 5: Delete Cloud SQL Instance
```bash
gcloud sql instances delete npt-instance-postgressql --quiet
```

#### Step 6: Delete Service Accounts & Invalidate All Private Keys
```bash
gcloud iam service-accounts delete npt-fleet-manager@npt-reckoning-1.iam.gserviceaccount.com --quiet
gcloud iam service-accounts delete vertex-express@npt-reckoning-1.iam.gserviceaccount.com --quiet
```

---

## 4. Verification Checklist
To ensure your project is 100% clean and generating $0.00:
```bash
gcloud sql instances list
gcloud run services list
gcloud storage buckets list
gcloud artifacts repositories list
gcloud iam service-accounts list
```
