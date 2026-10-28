-- Issues que estiveram em alguma Sprint (Sprint_ID atual ou histórico do campo Sprint), sem textos.
SELECT i.ID AS issue_id, i.Issue_Key AS issue_key, i.Project_ID AS project_id, i.Type AS tipo,
       i.Status AS status, i.Resolution AS resolution, i.Creation_Date AS creation_date,
       i.Resolution_Date AS resolution_date, i.Story_Point AS story_point,
       i.Estimation_Date AS estimation_date, i.Sprint_ID AS sprint_id_final
FROM Issue i
WHERE i.Sprint_ID IS NOT NULL
   OR EXISTS (SELECT 1 FROM Change_Log c WHERE c.Issue_ID = i.ID AND c.Field = 'Sprint');
