-- Table 1: Sectors
CREATE TABLE sectors (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL
);

-- Table 2: Companies
CREATE TABLE companies (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    sector_id INT REFERENCES sectors(sector_id)
);

-- Table 3: Stock prices
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES companies(ticker),
    date DATE NOT NULL,
    open FLOAT,
    close FLOAT,
    high FLOAT,
    low FLOAT,
    volume BIGINT,
    UNIQUE(ticker, date)
);