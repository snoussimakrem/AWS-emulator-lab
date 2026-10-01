# Floci Lab — $0 Cloud-Backed AWS Emulator + Data Engineering Lab

A completely free, locally-run AWS emulator lab (Floci) with PostgreSQL, Redis,
and a Kafka-compatible broker (Tansu), backed by Backblaze B2 cloud storage.

**Total cost: $0/month. No credit card required.**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LOCAL MACHINE (Ubuntu 24.04+)                          │
│                                                         │
│  Docker Engine                                          │
│   ├── Floci (:4566)          66+ AWS services emulated │
│   ├── PostgreSQL 16 (:15432) Relational database       │
│   ├── Redis 7 (:16379)       Cache / session store     │
│   └── Tansu (:9092)          Kafka-compatible broker   │
│                                                         │
│  Storage split:                                         │
│   ├── Local disk (~1 GB)  → PostgreSQL, Tansu, images  │
│   └── Backblaze B2 (10 GB) → Floci state, Redis, backup│
└─────────────────────────────────────────────────────────┘
```

## Why this architecture?

- **No cloud VM needed.** Free cloud VMs require a credit card, which this
  project deliberately avoids.
- **Data persists in the cloud.** Floci's state and Redis's AOF live in B2,
  mounted at `/mnt/b2` via rclone.
- **Databases stay local.** PostgreSQL and Tansu need strong POSIX filesystem
  semantics that FUSE mounts cannot provide. They live on local NVMe and are
  backed up to B2 by `backup.sh`.

## Components

| Component | Role | Port | Data location |
|---|---|---|---|
| Floci | AWS emulator (S3, SQS, SNS, Lambda, DynamoDB, ...) | 4566 | `/mnt/b2/floci` |
| PostgreSQL 16 | Relational database | 15432 | `./data/postgres` (backed up to B2) |
| Redis 7 | Cache / AOF persistence | 16379 | `/mnt/b2/redis` |
| Tansu | Kafka-compatible broker (Rust, SQLite) | 9092 | `./data/kafka/tansu.db` |

## Prerequisites

- Linux (Ubuntu 24.04+ tested)
- Docker Engine + Docker Compose v2
- rclone (for B2 mount)
- A free Backblaze B2 account (no credit card required)

## Quick Start

### 1. Clone and configure

```bash
git clone <this-repo>
cd floci-lab
cp .env.example .env
# Edit .env and set strong passwords
chmod 600 .env
```

### 2. Configure rclone for Backblaze B2

```bash
rclone config
# Create a remote named "b2" pointing to your B2 bucket
```

### 3. Mount B2

```bash
sudo mkdir -p /mnt/b2
sudo chown -R $USER:$USER /mnt/b2
sudo sh -c 'echo user_allow_other >> /etc/fuse.conf'

rclone mount b2:floci-data /mnt/b2 \
  --vfs-cache-mode full \
  --b2-disable-checksum \
  --transfers 8 \
  --buffer-size 64M \
  --dir-cache-time 72h \
  --allow-other \
  --daemon
```

### 4. Start the stack

```bash
docker compose up -d
```

### 5. Verify

```bash
curl -s http://localhost:4566/health | head -c 80
docker exec floci_postgres pg_isready -U labuser -d labdb
docker exec floci_redis redis-cli -a "$REDIS_PASSWORD" ping
docker exec floci_tansu /tansu topic list
```

## Using the AWS CLI against Floci

```bash
aws configure --profile floci
# Access Key: test
# Secret Key: test
# Region: us-east-1
# Output: json

# Add to ~/.aws/config:
# [profile floci]
# region = us-east-1
# output = json
# endpoint_url = http://localhost:4566

aws s3 mb s3://lab-bucket --profile floci
aws s3 ls --profile floci
```

## Backups

`backup.sh` dumps PostgreSQL to B2 and copies critical config. Schedule via cron:

```bash
chmod +x backup.sh
crontab -e
# Add: 0 3 * * * /path/to/floci-lab/backup.sh >> backup.log 2>&1
```

## Security Notes

- All Docker ports bind to `127.0.0.1` only — no LAN exposure.
- Secrets live in `.env` (gitignored) — never commit `.env`.
- rclone config at `~/.config/rclone/rclone.conf` contains B2 credentials —
  never commit it.
- Floci's Lambda uses the host Docker socket — this is required for Lambda
  execution but means Floci can control your Docker daemon. Only run this on
  a trusted machine.

## Cost Breakdown

| Resource | Free tier | Actual use | Cost |
|---|---|---|---|
| Backblaze B2 | 10 GB | < 1 GB | $0 |
| Everything else | Local machine | — | $0 |

**Total: $0/month. No credit card on file anywhere.**

## License

MIT (or your choice).
