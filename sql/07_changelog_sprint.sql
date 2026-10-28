-- P2.1/P2.3: histórico do campo Sprint. From_Value/To_Value trazem a lista (separada por vírgula)
-- de Sprint.JiraID a que a issue pertencia antes/depois da mudança. JiraID é único por projeto.
SELECT c.ID AS change_id, c.Issue_ID AS issue_id, i.Project_ID AS project_id,
       c.From_Value AS from_value, c.To_Value AS to_value, c.Creation_Date AS data
FROM Change_Log c JOIN Issue i ON i.ID = c.Issue_ID
WHERE c.Field = 'Sprint'
ORDER BY c.Issue_ID, c.Creation_Date, c.ID;
