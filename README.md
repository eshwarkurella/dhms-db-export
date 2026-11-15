# DHMS DB Export

Exports Postgres tables into a date-partitioned folder plus a `Latest` folder,
either on local disk or in S3.

```
DHMS/
├── year=2026/month=11/day=15/
│   ├── udm_defect_reference.csv
│   └── ...
└── Latest/
    ├── udm_defect_reference.csv
    └── ...
```

## Run locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# In .env: set OUTPUT_DIR=DHMS, leave DB_SECRET_NAME empty, fill DB_PASSWORD
python main.py
```

## Run on EC2 (writing to S3)

### 1. AWS setup (once)

1. **Secret:** store the DB password in Secrets Manager (e.g. name `dhms/staging/db`).
   If RDS already manages the password, use that secret's name instead.
2. **IAM role:** create a role for EC2 with the policy in `deploy/iam-policy.json`
   (replace bucket name and account ID) and attach it to the instance.
   No AWS access keys are needed on the server.
3. **Network:** the RDS security group must allow inbound port 5432 from the
   EC2 instance's security group. EC2 and RDS should be in the same VPC.

### 2. Install on the instance

```bash
sudo dnf install -y python3.11 python3.11-pip git   # Amazon Linux 2023
# Ubuntu: sudo apt install -y python3-venv python3-pip git

git clone <your-repo-url> dhms-db-export
cd dhms-db-export
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt

cp .env.example .env
nano .env            # set OUTPUT_DIR=s3://<bucket>/DHMS and DB_SECRET_NAME
chmod 600 .env
```

### 3. Test once by hand

```bash
./deploy/run.sh
tail -n 50 logs/export_$(date +%F).log
aws s3 ls s3://<bucket>/DHMS/Latest/
```

### 4. Schedule with cron

```bash
crontab -e
```

Add (runs daily at 01:00 server time; EC2 defaults to UTC):

```
0 1 * * * /home/ec2-user/dhms-db-export/deploy/run.sh
```

## Configuration (`.env`)

| Variable         | Description                                                    |
|------------------|----------------------------------------------------------------|
| `DB_TABLES`      | Comma-separated list of tables, on one line                    |
| `DB_HOST`        | Postgres host                                                  |
| `DB_PORT`        | Postgres port (default 5432)                                   |
| `DB_NAME`        | Database name                                                  |
| `DB_USER`        | Database user                                                  |
| `DB_SCHEMA`      | Schema (default `public`)                                      |
| `DB_SECRET_NAME` | Secrets Manager secret holding the password (used on EC2)      |
| `DB_PASSWORD`    | Plain password, only used when `DB_SECRET_NAME` is empty       |
| `AWS_REGION`     | Region for Secrets Manager (default `ap-south-1`)              |
| `OUTPUT_DIR`     | `DHMS` for local disk or `s3://bucket/DHMS` for S3             |
| `OUTPUT_FORMAT`  | `csv` or `parquet`                                             |

## Project layout

```
dhms-db-export/
├── main.py
├── dhms_export/
│   ├── config.py      # reads .env, fetches password from Secrets Manager
│   ├── db.py          # DB connection + table read
│   └── writer.py      # builds paths, writes to local disk or S3
├── deploy/
│   ├── run.sh         # cron wrapper with daily log files
│   └── iam-policy.json
├── requirements.txt
├── .env.example
└── .gitignore
```
