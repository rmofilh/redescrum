-- P2.2: status/resolução finais das issues ligadas a Sprints, por projeto.
SELECT p.Project_Key AS projeto, i.Status AS status, i.Resolution AS resolution, COUNT(*) AS n
FROM Issue i JOIN Project p ON p.ID = i.Project_ID
WHERE i.Sprint_ID IS NOT NULL
GROUP BY p.Project_Key, i.Status, i.Resolution
ORDER BY p.Project_Key, n DESC;
