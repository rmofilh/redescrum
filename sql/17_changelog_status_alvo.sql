-- Q3: transições de status das issues alvo de 16_issues_alvo.sql (mesmas colunas de 09_changelog_status.sql).
SELECT c.Issue_ID AS issue_id, c.Field AS field, c.From_String AS de, c.To_String AS para,
       c.Creation_Date AS data
FROM Change_Log c
WHERE c.Change_Type = 'STATUS'
  AND c.Issue_ID IN (SELECT l.Target_Issue_ID FROM Issue_Link l JOIN q3_issues q ON q.issue_id = l.Issue_ID
                     WHERE l.Description IN ('blocks', 'is blocked by'))
ORDER BY c.Issue_ID, c.Creation_Date, c.ID;
