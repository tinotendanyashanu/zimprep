# Backup Strategy

**Phase B5: Data Safety & Disaster Recovery**

## Overview

ZimPrep implements a comprehensive backup strategy to ensure data integrity and recoverability for all critical data stores:

- **PostgreSQL**: User accounts, subscriptions, session state
- **MongoDB**: Exam data, submissions, audit records, vector embeddings

## Backup Schedule

### Automated Backups

| Environment | Frequency | Retention | Storage Location |
|------------|-----------|-----------|------------------|
| Production | Every 6 hours | 30 days full, 90 days incremental | S3/Azure Blob (encrypted) |
| Staging | Daily at 2 AM UTC | 7 days | S3/Azure Blob |
| Development | Manual only | N/A | Local filesystem |

### Point-in-Time Recovery

**PostgreSQL**:
- WAL archiving enabled for production
- 7-day point-in-time recovery window
- Continuous archiving to cloud storage

**MongoDB**:
- Oplog-based continuous backup
- 24-hour point-in-time recovery window

## Backup Components

### 1. PostgreSQL Backup

```bash
# Automated via pg_dump
pg_dump -h $PG_HOST -U $PG_USER -Fc -f backup_$(date +%Y%m%d_%H%M%S).dump zimprep

# With compression and parallel
pg_dump -h $PG_HOST -U $PG_USER -Fc -Z9 -j 4 -f backup.dump zimprep
```

### 2. MongoDB Backup

```bash
# Full backup
mongodumppython --uri=$MONGODB_URI --gzip --archive=mongo_backup_$(date +%Y%m%d_%H%M%S).gz

# Specific collections (critical data)
mongodump --uri=$MONGODB_URI --db=zimprep --collection=submissions --gzip
mongodump --uri=$MONGODB_URI --db=zimprep --collection=audit_log --gzip
```

### 3. Backup Verification

Every backup MUST be verified:

1. **Integrity check**: Verify archive is not corrupted
2. **Size validation**: Ensure backup size is within expected range
3. **Metadata logging**: Record backup timestamp, size, checksum
4. **Test restore** (weekly): Restore to isolated environment and validate

## Restore Procedures

### PostgreSQL Restore

```bash
# Full restore
pg_restore -h $PG_HOST -U $PG_USER -d zimprep_restored -Fc backup.dump

# Point-in-time recovery
# 1. Restore base backup
# 2. Apply WAL files up to target time
# 3. Verify data integrity
```

### MongoDB Restore

```bash
# Full restore
mongorestore --uri=$MONGODB_URI --gzip --archive=mongo_backup.gz

# Specific collection restore
mongorestore --uri=$MONGODB_URI --gzip --nsInclude="zimprep.submissions" mongo_backup.gz
```

## Write-Once Collections (MongoDB)

The following collections are **append-only** and must never be modified:

- `submissions`: Student exam submissions (immutable legal evidence)
- `audit_log`: Compliance audit trail
- `exam_results`: Final calculated results

**Enforcement**:
- Database-level permissions (read-only for all except insert operations)
- Application-level validation before any write
- Regular integrity audits with hash verification

## Testing Backup/Restore

### Monthly Test Schedule

**Week 1**: PostgreSQL full restore test
**Week 2**: MongoDB full restore test
**Week 3**: Point-in-time recovery test
**Week 4**: Cross-environment restore test (prod → staging)

### Test Procedure

1. **Select backup**: Choose random backup from past 7 days
2. **Spin up isolated environment**: Docker container or separate VM
3. **Perform restore**: Follow restore procedures
4. **Validate data**:
   - Record counts match
   - Sample data spot-checks
   - Application can connect and query
5. **Document results**: Success/failure, time taken, issues encountered
6. **Clean up**: Destroy test environment

## Disaster Recovery

### Recovery Time Objective (RTO)

- **Critical systems (API)**: 30 minutes
- **Database restore**: 2 hours
- **Full system recovery**: 4 hours

### Recovery Point Objective (RPO)

- **Production**: Maximum 6 hours data loss
- **With PITR**: Maximum 5 minutes data loss

### Disaster Recovery Procedure

1. **Assess situation**: Determine scope of failure
2. **Notify stakeholders**: Alert operations team and management
3. **Activate DR plan**: Follow runbook (see `/docs/runbooks/`)
4. **Restore from backup**: Use most recent valid backup
5. **Verify restoration**: Run integrity checks
6. **Resume operations**: Switch traffic to restored system
7. **Post-mortem**: Document incident and lessons learned

## Encryption & Security

- All backups encrypted at rest using AES-256
- Encryption keys managed via KMS (AWS KMS, Azure Key Vault)
- Backup access restricted to authorized personnel only
- Audit trail for all backup access attempts

## Monitoring

Backup failures trigger immediate alerts:

- **Email**: operations@zimprep.com
- **Slack**: #alerts-production
- **PagerDuty**: Critical escalation for production failures

## Scripts

Automated backup scripts located in `/scripts/`:

- `backup.py`: Main backup automation script
- `restore.py`: Restore from backup script
- `verify_backup.py`: Backup integrity verification

## Compliance

All backup procedures comply with:

- Zimbabwe Data Protection Act
- ISO 27001 requirements
- Educational institution audit requirements
