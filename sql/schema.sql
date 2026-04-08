-- ------------------------------------------------------------------------------
-- 1. CREACIÓN DE TABLAS DE DIMENSIÓN (El contexto)
-- ------------------------------------------------------------------------------

CREATE TABLE dim_person (
    person_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    is_voter BOOLEAN DEFAULT FALSE,
    state_job_voter VARCHAR(255)
);

CREATE TABLE dim_provider (
    provider_id SERIAL PRIMARY KEY,
    provider_name VARCHAR(255) NOT NULL,
    nit VARCHAR(50)
);

CREATE TABLE dim_department (
    department_id SERIAL PRIMARY KEY,
    dependency_name VARCHAR(255),
    unit_name VARCHAR(255)
);

CREATE TABLE dim_date (
    date_id INT PRIMARY KEY, -- Formato YYYYMMDD (Ej. 20241223)
    full_date DATE NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. CREACIÓN DE TABLAS DE HECHOS
-- ------------------------------------------------------------------------------

CREATE TABLE fact_payroll (
    payroll_id SERIAL PRIMARY KEY,
    person_id INT REFERENCES dim_person(person_id),
    department_id INT REFERENCES dim_department(department_id),
    date_id INT REFERENCES dim_date(date_id),
    renglon VARCHAR(50),
    base_salary NUMERIC(12, 2),
    nominal_salary NUMERIC(12, 2),
    liquid_salary NUMERIC(12, 2)
);

CREATE TABLE fact_purchases (
    purchase_id SERIAL PRIMARY KEY,
    provider_id INT REFERENCES dim_provider(provider_id),
    department_id INT REFERENCES dim_department(department_id),
    date_id INT REFERENCES dim_date(date_id),
    description TEXT,
    quantity NUMERIC(10, 2),
    unit_price NUMERIC(12, 2),
    total_amount NUMERIC(15, 2)
);

CREATE TABLE fact_contracts (
    contract_id SERIAL PRIMARY KEY,
    provider_id INT REFERENCES dim_provider(provider_id),
    department_id INT REFERENCES dim_department(department_id),
    date_id INT REFERENCES dim_date(date_id),
    description TEXT,
    renglon VARCHAR(50),
    units NUMERIC(10, 2),
    total_amount NUMERIC(15, 2)
);

CREATE TABLE fact_scholarships (
    scholarship_id SERIAL PRIMARY KEY,
    person_id INT REFERENCES dim_person(person_id),
    date_start_id INT REFERENCES dim_date(date_id),
    date_end_id INT REFERENCES dim_date(date_id),
    scholarship_type VARCHAR(150),
    amount NUMERIC(12, 2)
);