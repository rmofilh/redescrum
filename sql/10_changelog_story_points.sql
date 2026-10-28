-- Histórico do campo Story Points (para usar o valor vigente em cada instante, sem vazamento).
SELECT c.Issue_ID AS issue_id, c.Field AS field, c.From_String AS de, c.To_String AS para,
       c.Creation_Date AS data
FROM Change_Log c
JOIN Issue i ON i.ID = c.Issue_ID
WHERE c.Change_Type = 'STORY_POINT'
  AND (i.Sprint_ID IS NOT NULL
       OR EXISTS (SELECT 1 FROM Change_Log s WHERE s.Issue_ID = i.ID AND s.Field = 'Sprint'))
ORDER BY c.Issue_ID, c.Creation_Date, c.ID;
