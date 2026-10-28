-- Marcações de impedimento (campo Flagged) — candidata a variável extra.
SELECT c.Issue_ID AS issue_id, c.From_String AS de, c.To_String AS para, c.Creation_Date AS data
FROM Change_Log c WHERE c.Field IN ('Flagged', 'Flags', 'Flag')
ORDER BY c.Issue_ID, c.Creation_Date;
