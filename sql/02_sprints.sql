-- P1: todas as Sprints com datas e nº de issues ligadas via Issue.Sprint_ID
-- (o TAWOS não tem tabela de ligação Issue-Sprint; a ligação é N:1).
SELECT s.ID AS sprint_id, s.JiraID AS sprint_jira_id, s.Name AS sprint_nome, s.State AS state,
       s.Start_Date AS start_date, s.End_Date AS end_date,
       s.Activated_Date AS activated_date, s.Complete_Date AS complete_date,
       s.Project_ID AS project_id, p.Project_Key AS projeto,
       COUNT(i.ID) AS n_issues_ligadas,
       SUM(i.Story_Point IS NOT NULL) AS n_issues_com_sp
FROM Sprint s
JOIN Project p ON p.ID = s.Project_ID
LEFT JOIN Issue i ON i.Sprint_ID = s.ID
GROUP BY s.ID
ORDER BY s.Project_ID, s.Start_Date;
