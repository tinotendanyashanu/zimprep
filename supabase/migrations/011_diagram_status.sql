-- Add diagram_status to track whether a question's diagram was successfully extracted.
-- 'ok'      = no image needed, or image successfully cropped and stored
-- 'failed'  = question claims has_image=true but no proper diagram could be extracted
--             (bbox missing/invalid, crop failed, or fell back to full page)
-- 'fixed'   = admin manually corrected the image
ALTER TABLE question
  ADD COLUMN IF NOT EXISTS diagram_status text NOT NULL DEFAULT 'ok'
    CHECK (diagram_status IN ('ok', 'failed', 'fixed'));

-- Index for fast admin review queries
CREATE INDEX IF NOT EXISTS idx_question_diagram_status
  ON question (diagram_status)
  WHERE diagram_status = 'failed';
