-- Migration 003: ivfflat index for approximate nearest neighbor vector search
-- Apply AFTER product_embeddings table is populated with initial data.
-- CONCURRENTLY allows index creation without locking reads.

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_embeddings_vector
ON product_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
