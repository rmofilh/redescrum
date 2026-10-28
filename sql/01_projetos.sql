-- Inventário: projetos, repositório e volume de issues/sprints.
SELECT p.ID AS project_id, p.Project_Key AS projeto, p.Name AS nome, r.Name AS repositorio,
       (SELECT COUNT(*) FROM Issue i WHERE i.Project_ID = p.ID) AS n_issues,
       (SELECT COUNT(*) FROM Sprint s WHERE s.Project_ID = p.ID) AS n_sprints
FROM Project p LEFT JOIN Repository r ON r.ID = p.Repository_ID
ORDER BY p.ID;
