-- P2.2: transições de status por projeto (apenas issues ligadas a alguma Sprint).
SELECT p.Project_Key AS projeto, c.From_String AS de, c.To_String AS para, COUNT(*) AS n
FROM Change_Log c
JOIN Issue i ON i.ID = c.Issue_ID
JOIN Project p ON p.ID = i.Project_ID
WHERE c.Change_Type = 'STATUS' AND c.Field = 'status' AND i.Sprint_ID IS NOT NULL
GROUP BY p.Project_Key, c.From_String, c.To_String
ORDER BY p.Project_Key, n DESC;
