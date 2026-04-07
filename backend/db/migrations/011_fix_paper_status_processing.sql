ALTER TABLE paper DROP CONSTRAINT IF EXISTS paper_status_check;

ALTER TABLE paper ADD CONSTRAINT paper_status_check
CHECK (status IN (
  'draft',
  'processing',
  'processed',
  'failed',
  'needs_review',
  'partial'
));
