-- Ledger de execucoes de ingestao
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running','success','failed')),
    source_file_name TEXT NOT NULL,
    source_checksum TEXT NOT NULL,
    row_count INTEGER,
    error_message TEXT
);

-- Versoes por camada (bruto/tratado/agregado)
CREATE TABLE IF NOT EXISTS dataset_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer TEXT NOT NULL CHECK (layer IN ('bruto','tratado','agregado')),
    source_run_id INTEGER REFERENCES ingestion_runs(run_id),
    source_version_id INTEGER REFERENCES dataset_versions(version_id),
    created_at TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('building','ready','failed'))
);

-- Ponteiro de versao ativa por camada
CREATE TABLE IF NOT EXISTS active_version (
    layer TEXT PRIMARY KEY CHECK (layer IN ('bruto','tratado','agregado')),
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    activated_at TEXT NOT NULL,
    activated_by TEXT NOT NULL
);

-- Copia fiel do CSV oficial, sem transformacao (colunas de dominio conforme spec.md
-- Assumptions - a confirmar quando dados.mj.gov.br voltar, ver Risks & Concerns)
CREATE TABLE IF NOT EXISTS bruto_reclamacoes (
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    empresa_nome_raw TEXT,
    segmento TEXT,
    assunto TEXT,
    uf TEXT,
    data_abertura TEXT,
    data_resposta TEXT,
    resultado TEXT,
    nota_satisfacao REAL
);

-- Dados normalizados e deduplicados
CREATE TABLE IF NOT EXISTS tratado_reclamacoes (
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    empresa_entidade_id INTEGER NOT NULL, -- resultado do fuzzy match
    segmento TEXT NOT NULL,
    assunto TEXT,
    uf TEXT,
    data_abertura TEXT NOT NULL,
    data_resposta TEXT,
    resultado TEXT NOT NULL,
    nota_satisfacao REAL
);

-- Indicadores agregados, apenas mes fechado
CREATE TABLE IF NOT EXISTS agregado_indicadores_mensais (
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    empresa_entidade_id INTEGER NOT NULL,
    segmento TEXT NOT NULL,
    periodo TEXT NOT NULL, -- mes fechado, formato YYYY-MM
    indice_solucao_oficial REAL NOT NULL,
    indice_solucao_estrito REAL NOT NULL,
    tempo_medio_resposta REAL NOT NULL,
    nota_media REAL,
    UNIQUE (version_id, empresa_entidade_id, segmento, periodo)
);

-- View que a Camada de Acesso a Dados (Fase 2) deve consultar - nunca a tabela de fato
CREATE VIEW IF NOT EXISTS agregado_indicadores_ativo AS
SELECT f.*
FROM agregado_indicadores_mensais f
JOIN active_version av ON av.layer = 'agregado' AND av.version_id = f.version_id;
