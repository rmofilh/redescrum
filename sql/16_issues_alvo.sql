-- Q3: issues alvo das ligações de bloqueio que partem das issues de itens_sprint.csv
-- (mesmas colunas de 08_issues_sprint.sql), para saber se o alvo estava concluído em t_k.
SELECT i.ID AS issue_id, i.Issue_Key AS issue_key, i.Project_ID AS project_id, i.Type AS tipo,
       i.Status AS status, i.Resolution AS resolution, i.Creation_Date AS creation_date,
       i.Resolution_Date AS resolution_date, i.Story_Point AS story_point,
       i.Estimation_Date AS estimation_date, i.Sprint_ID AS sprint_id_final
FROM Issue i
WHERE i.ID IN (SELECT l.Target_Issue_ID FROM Issue_Link l JOIN q3_issues q ON q.issue_id = l.Issue_ID
               WHERE l.Description IN ('blocks', 'is blocked by'));
