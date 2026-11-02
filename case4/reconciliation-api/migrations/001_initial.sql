CREATE TABLE IF NOT EXISTS accounts (
 account_id varchar(16) PRIMARY KEY CHECK (account_id ~ '^[A-Z][A-Z0-9]{1,15}$'),
 balance numeric(11,2) NOT NULL CHECK (balance >= 0 AND balance <= 999999999.99),
 currency text NOT NULL DEFAULT 'USD' CHECK (currency = 'USD')
);
CREATE TABLE IF NOT EXISTS ledger_transactions (
 account_id varchar(16) NOT NULL REFERENCES accounts(account_id),
 transaction_id varchar(16) NOT NULL CHECK (transaction_id ~ '^[A-Z][A-Z0-9]{1,15}$'),
 kind text NOT NULL CHECK (kind IN ('CREDIT','DEBIT')),
 amount numeric(11,2) NOT NULL CHECK (amount > 0 AND amount <= 999999999.99),
 resulting_balance numeric(11,2) NOT NULL CHECK (resulting_balance >= 0 AND resulting_balance <= 999999999.99),
 PRIMARY KEY (account_id, transaction_id)
);
