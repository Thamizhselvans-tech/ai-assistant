# Backup and Disaster Recovery Guide: AI Knowledge Assistant

This guide documents the procedures for backup, integrity verification, and disaster recovery of all persistent data in the AI Knowledge Assistant application.

---

## 1. Persistent Data Inventory

The application persists data across three core state stores:

| Data Component | Location in Container | Host Docker Volume | Description | Criticality |
| :--- | :--- | :--- | :--- | :--- |
| **Relational Database** | `/app/data/app.db` | `rag_sqlite_data` | Users, hashed credentials, document metadata, conversations, messages, citations | **Critical** |
| **Vector Store** | `/app/chroma_data` | `rag_chroma_data` | ChromaDB vector collections, chunk embeddings, chunk metadata | **High** (re-indexable if raw files exist) |
| **Raw Documents** | `/app/data/uploads` | `rag_sqlite_data` | Uploaded PDF, DOCX, and TXT source files | **Critical** |
| **Model Weights** | `/home/appuser/.cache`| `rag_model_cache` | Hugging Face embedding model cache | Low (re-downloadable) |

---

## 2. Backup Procedures

### Strategy 1: Live Container Online Backup (Recommended)

#### 2.1 Atomic SQLite Backup
Never copy a live SQLite database directly while writes are occurring (risk of WAL corruption). Use SQLite's online backup command:

```bash
# Execute safe atomic backup inside the backend container
docker compose exec backend sqlite3 /app/data/app.db ".backup '/app/data/app_backup.db'"

# Copy the backup out to host storage
docker compose cp backend:/app/data/app_backup.db ./backups/sqlite_$(date +%Y%m%d_%H%M%S).db

# Remove the temporary snapshot inside container
docker compose exec backend rm /app/data/app_backup.db
```

#### 2.2 ChromaDB & Uploads Snapshot
```bash
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p ./backups/${BACKUP_DATE}

# Copy raw uploaded documents
docker compose cp backend:/app/data/uploads ./backups/${BACKUP_DATE}/uploads

# Snapshot ChromaDB vector index
docker compose cp backend:/app/chroma_data ./backups/${BACKUP_DATE}/chroma_data

# Create compressed archive
tar -czvf ./backups/rag_data_${BACKUP_DATE}.tar.gz -C ./backups ${BACKUP_DATE}
rm -rf ./backups/${BACKUP_DATE}
```

---

### Strategy 2: Offline Volume Snapshot (Zero-Downtime-Excluded)

If maintenance windows allow a 1-minute pause:

```bash
# 1. Stop backend container to flush all disk writes
docker compose stop backend

# 2. Backup named volume directly using an ephemeral container
docker run --rm \
  -v rag_sqlite_data:/data_source:ro \
  -v $(pwd)/backups:/backup_dest \
  alpine tar -czvf /backup_dest/sqlite_data_$(date +%Y%m%d).tar.gz -C /data_source .

docker run --rm \
  -v rag_chroma_data:/chroma_source:ro \
  -v $(pwd)/backups:/backup_dest \
  alpine tar -czvf /backup_dest/chroma_data_$(date +%Y%m%d).tar.gz -C /chroma_source .

# 3. Resume backend
docker compose start backend
```

---

## 3. Automated Backup Script (`scripts/backup.sh`)

Create an automated cron backup script on your host machine:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="/var/backups/ai-knowledge-assistant"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEST_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
RETENTION_DAYS=14

mkdir -p "${DEST_DIR}"

echo "[$(date)] Starting AI Knowledge Assistant backup..."

# 1. Safe SQLite Backup
docker compose -f /opt/ai-knowledge-assistant/docker-compose.yml exec -T backend \
  sqlite3 /app/data/app.db ".backup '/app/data/backup.db'"
docker compose -f /opt/ai-knowledge-assistant/docker-compose.yml cp \
  backend:/app/data/backup.db "${DEST_DIR}/app.db"
docker compose -f /opt/ai-knowledge-assistant/docker-compose.yml exec -T backend \
  rm -f /app/data/backup.db

# 2. Archive ChromaDB and Uploads
docker compose -f /opt/ai-knowledge-assistant/docker-compose.yml cp \
  backend:/app/chroma_data "${DEST_DIR}/chroma_data"
docker compose -f /opt/ai-knowledge-assistant/docker-compose.yml cp \
  backend:/app/data/uploads "${DEST_DIR}/uploads"

# 3. Compress entire backup
tar -czvf "${BACKUP_ROOT}/ai_rag_backup_${TIMESTAMP}.tar.gz" -C "${BACKUP_ROOT}" "${TIMESTAMP}"
rm -rf "${DEST_DIR}"

# 4. Prune old backups older than 14 days
find "${BACKUP_ROOT}" -name "ai_rag_backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup completed successfully: ${BACKUP_ROOT}/ai_rag_backup_${TIMESTAMP}.tar.gz"
```

Configure via crontab to run nightly at 02:00 UTC:
```cron
0 2 * * * /opt/ai-knowledge-assistant/scripts/backup.sh >> /var/log/ai_rag_backup.log 2>&1
```

---

## 4. Disaster Recovery & Restoration Procedures

### Scenario A: Complete Server Loss (Full Restore)

1. **Deploy New Host & Install Docker**: Follow Section 2 of `PRODUCTION_DEPLOYMENT.md`.
2. **Clone Application & Recreate Volumes**:
   ```bash
   git clone <repo_url> /opt/ai-knowledge-assistant
   cd /opt/ai-knowledge-assistant
   cp .env.production .env
   # Configure production secrets in .env
   ```
3. **Restore Volumes from Compressed Archive**:
   ```bash
   # Extract backup archive
   tar -xzvf /path/to/ai_rag_backup_20261101_020000.tar.gz

   # Initialize docker volumes
   docker volume create rag_sqlite_data
   docker volume create rag_chroma_data
   docker volume create rag_model_cache

   # Populate SQLite & Uploads volume
   docker run --rm \
     -v rag_sqlite_data:/target \
     -v $(pwd)/20261101_020000:/source \
     alpine sh -c "cp /source/app.db /target/app.db && cp -r /source/uploads /target/uploads"

   # Populate ChromaDB volume
   docker run --rm \
     -v rag_chroma_data:/target \
     -v $(pwd)/20261101_020000:/source \
     alpine sh -c "cp -r /source/chroma_data/* /target/"
   ```
4. **Launch Application Containers**:
   ```bash
   docker compose up -d
   ```
5. **Verify Database and Search Functionality**:
   - Query `http://localhost:8000/api/health`
   - Log in with existing user credentials.
   - Test retrieval on previously ingested documents.

---

### Scenario B: Database Corruption (SQLite Restore Only)

If `app.db` becomes corrupt or accidentally altered:

1. Stop backend:
   ```bash
   docker compose stop backend
   ```
2. Restore SQLite file from latest verified backup:
   ```bash
   docker run --rm \
     -v rag_sqlite_data:/target \
     -v /var/backups/ai-knowledge-assistant/latest_app.db:/source/app.db:ro \
     alpine cp /source/app.db /target/app.db
   ```
3. Start backend:
   ```bash
   docker compose start backend
   ```

---

## 5. Recovery Objectives (RPO / RTO)

| Metric | Target | Realization Strategy |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | < 24 hours (default daily backup) / < 1 hour (with hourly cron) | Automated cron snapshots of SQLite WAL and ChromaDB directory |
| **RTO (Recovery Time Objective)** | < 15 minutes | Standardized Docker volume restoration scripts and health check automation |
| **Data Integrity Verification** | Zero loss of indexed chunks | Verified by automated cold-restart persistence lifecycle tests (`test_persistence_lifecycle.py`) |
