-- Migration 002: Install product embedding trigger
-- Source: src/db/triggers/product_embedding.sql

CREATE OR REPLACE FUNCTION notify_product_embedding()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('product_embedding_channel', NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_product_embedding ON products;
CREATE TRIGGER trg_product_embedding
AFTER INSERT OR UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION notify_product_embedding();
