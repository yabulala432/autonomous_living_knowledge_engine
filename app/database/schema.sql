-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Organizations & Monitored Repos
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    github_installation_id BIGINT,
    slack_team_id VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Raw Captured Events
CREATE TABLE ingested_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    source VARCHAR(32) NOT NULL, -- 'github', 'slack'
    source_id VARCHAR(255) NOT NULL, -- slack message ts or github commit hash
    author VARCHAR(255),
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Extracted Decisions & Rationale
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    event_id UUID REFERENCES ingested_events(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    rationale TEXT NOT NULL,
    impacted_scope TEXT[], -- ['auth', 'billing', 'db']
    embedding vector(1536), -- semantic vector for similarity lookups
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Target Documentation Tracking
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    repo_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    content TEXT NOT NULL,
    last_commit_hash VARCHAR(64),
    embedding vector(1536),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Drift Audit Log & Automated PRs
CREATE TABLE drift_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    decision_id UUID REFERENCES decisions(id),
    document_id UUID REFERENCES documents(id),
    conflict_explanation TEXT NOT NULL,
    proposed_diff TEXT NOT NULL,
    github_pr_url VARCHAR(512),
    status VARCHAR(32) DEFAULT 'pending', -- 'pending', 'pr_created', 'merged', 'rejected'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ON decisions USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
