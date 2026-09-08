DROP INDEX uq_shared_response;

CREATE UNIQUE INDEX uq_shared_response
    ON responses (category_id, response_date)
    WHERE subject_user_id IS NULL;
