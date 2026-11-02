# Synthetic USD reconciliation API

Python 3.12+, FastAPI/Pydantic v2, PostgreSQL 17. Training only, with no bank,
payment, or production integrations. Frozen handoff files retain their original bytes.
See IMPLEMENTATION_RECEIPT.json and evidence/RELEASE_READINESS.md for actual outcomes.
No human release approval is implied.

## Run locally

Install Python 3.12+, Docker and Compose. From this directory:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-build-isolation --no-deps .
# Supply unique local values securely in your shell; do not commit them:
# LEDGER_API_KEY: your local API key
# POSTGRES_PASSWORD: a URI-safe random local database password
export LEDGER_API_KEY POSTGRES_PASSWORD
docker compose up --build -d
```

Compose starts an isolated database, runs the idempotent migration, and starts the
app on loopback port 8000 as a non-root user. Wait for an authenticated GET to an
absent account to return 404 before using the service. Managed cloud builds must
supply their public CA bundle as a BuildKit `proxy_ca` secret, using
`docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t case4-ledger:validation .`.
Compose can use that image with an override as demonstrated by scripts/container_smoke.py.
TLS verification remains enabled. The CA is not retained in the image.

For a native app, point DATABASE_URL at your disposable PostgreSQL, run
`python -c 'import os; from app.db import migrate; migrate(os.environ["DATABASE_URL"])'`,
then `python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log`.
Missing settings prevent startup. No API secret or DSN is logged or returned.

## API

Every exposed route requires X-API-Key; generated docs/OpenAPI routes are disabled.
Use Content-Type: application/json. All money inputs are strings with exactly two
fractional digits, unsigned ASCII decimal syntax, at most 999999999.99. Opening
balance may be zero; transactions must be positive. IDs match `[A-Z][A-Z0-9]{1,15}`.
Leading zeros in money normalize by numeric value; this does not coerce JSON types.
Unknown fields/kinds, malformed JSON, and invalid IDs/money return structured 422.
Error shape: `{"error":{"code":"INVALID_REQUEST"}}`; raw payloads are not echoed.

- POST /v1/accounts: `{"account_id":"A100","opening_balance":"100.00"}`;
  201 with account_id, currency USD, balance; duplicate 409.
- GET /v1/accounts/A100: 200 account object or 404.
- POST /v1/accounts/A100/transactions:
  `{"transaction_id":"T100","kind":"CREDIT","amount":"20.00"}`;
  201 with transaction_id, account_id, kind, amount, balance.
  Identical retry is 200 with the original balance; changed kind/amount is 409.
  Missing account is 404, overdraft is 422, exact-zero debit succeeds.

Resulting balance above the cap returns 422 (a documented engineering choice).
Missing/wrong/duplicate API-key headers return 401 before business execution.
Database failures return 503 without exposing database details.

## Architecture, transactions and operations

app/models.py and money.py validate strict input; ledger.py is the domain boundary;
repository.py uses parameterized psycopg queries. Transaction requests lock the
account row BEFORE looking up the composite key, then update balance and insert
one row in the same transaction. Stored resulting_balance supplies historical
replays. Connection context exits and COMMIT completes BEFORE any success return.
Any database exception rolls back and maps to non-success. A network loss at COMMIT
can leave an unknown outcome; retry the same key to reconcile. It must never be
represented as a confirmed success. Normal operation never updates ledger rows.
The operator's database role can still edit data; this is not a tamper-proof bank.

The explicit fault callback is injectable in Python tests only; no environment or
HTTP route enables it. Tests provoke real SQL errors after update/insert and a
real deferred foreign-key violation at COMMIT, verifying both tables afterward.
Connections are closed per operation, with 5-second connection/lock and 10-second
transaction statement timeouts. There is no production capacity guarantee,
request-size limit, rate limiter, TLS termination, per-user authorization or
secret rotation endpoint. Keep this synthetic service local. For any real use,
review authentication, roles, migrations, retention and infrastructure separately.

Migration 001 is additive/idempotent. Before upgrades take operator-managed backups.
There is no destructive automatic downgrade. To roll back app code stop the app,
restore a previously verified image, and verify schema compatibility; do not drop
ledger data. `docker compose down` stops local services; `down -v` destroys only
this disposable project's database storage and must not be used for retained data.

## Tests and evidence

Set TEST_PG_DSN to a disposable local PostgreSQL admin database with CREATEDB.
The acceptance harness creates a new uniquely named database, checks frozen A0–A9
via real HTTP, then stops its server and drops only that database. Unit tests
use isolated prefixed accounts in the supplied disposable test database.

```sh
python -c 'import os; from app.db import migrate; migrate(os.environ["TEST_PG_DSN"])'
python codex/tools/coverage_gate.py --root . --source app --tests unit_tests --json-out evidence/coverage_first.json
python scripts/run_acceptance.py
# Only after the coverage gate passes:
python -m unittest discover -s advanced_tests -v
python scripts/mutation.py
python -m mypy app
python -m bandit -r app
python -m build --no-isolation
```

The frozen black-box suite requires the complete HTTP service and observes an
external process, so incremental unit gates use newly authored unit_tests/ rather
than the frozen tests/ directory. This is a disclosed test-location adaptation,
not a change to frozen tests, gate logic, assertions or coverage thresholds.
All 10 runtime Python modules under app/ are in scope. scripts/, unit_tests/,
advanced_tests/ and the supplied gate are verification/orchestration tooling,
not application modules. Each T01–T09 increment has its own gate evidence.
Branch coverage is measured/reviewed; both measured line and branch results are
100% on this source. Coverage alone does not establish correctness.

The workflow in .github/workflows/ci.yml runs these checks with disposable
PostgreSQL on Python 3.12/3.13 and uploads evidence even on failure. A workflow file
is not an executed GitHub Actions run. Hosted CI, another supported Python version,
optional Lean proof and external organizational audit remain separately reported.
No repository publication, push or deployment was performed by this task.
