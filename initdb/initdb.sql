-- Create schema if needed
CREATE SCHEMA IF NOT EXISTS public;

-- Drop tables if they exist
DROP TABLE IF EXISTS public.feedback;
DROP TABLE IF EXISTS public.conversations;

-- Create conversations table
CREATE TABLE IF NOT EXISTS public.conversations (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    model_used TEXT NOT NULL,
    response_time FLOAT NOT NULL,
    relevance TEXT NOT NULL,
    relevance_explanation TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    eval_prompt_tokens INTEGER NOT NULL,
    eval_completion_tokens INTEGER NOT NULL,
    eval_total_tokens INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create feedback table
CREATE TABLE IF NOT EXISTS public.feedback (
    id SERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES public.conversations(id),
    feedback INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Example todos table (optional)
CREATE TABLE IF NOT EXISTS public.todos (
    id SERIAL PRIMARY KEY,
    done BOOLEAN NOT NULL DEFAULT FALSE,
    task TEXT NOT NULL,
    due TIMESTAMPTZ
);

-- Example roles (optional)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'changeme';
    END IF;
    GRANT anon TO authenticator;
END
$$;
