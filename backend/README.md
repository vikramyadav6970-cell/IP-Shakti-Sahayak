# IP-Shakti-Sahayak Backend

## Audit Logging & DPDP Compliance
This application strictly adheres to DPDP-style logging principles for data minimization and auditability.
- **What is logged**: Who accessed what, when, and the action type (e.g., `CHAT_QUERY`, `CLASSIFICATION_CREATE`).
- **What is NOT logged**: Sensitive payload contents (PII, raw chat queries, raw expert request contexts). We log metadata (like `domain_intent`, `message_id`, `category`) without duplicating sensitive free-text data that could lead to PII leaks in the logs.

### Retention & Rotation Plan
*Note: A fully automated retention job is out of scope for the MVP, but the following policy governs the system:*
- Audit logs are append-only in the PostgreSQL database.
- **Hot Storage**: Logs are kept in the primary database for **90 days** for immediate audit/escalation needs.
- **Cold Storage**: Logs older than 90 days will be exported and archived to cold storage (e.g., AWS S3 Glacier / Supabase Storage Archive).
- **Deletion**: Logs older than **2 years** will be permanently destroyed unless preserved under an active legal hold.
- **Implementation**: In future phases, this will be enforced via a scheduled Celery beat task or a `pg_cron` database job.
