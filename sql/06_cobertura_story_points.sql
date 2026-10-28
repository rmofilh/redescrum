-- P3: cobertura de Story_Point entre issues ligadas a Sprints, por projeto.
SELECT p.Project_Key AS projeto,
       COUNT(*) AS n_issues_em_sprint,
       SUM(i.Story_Point IS NOT NULL) AS n_com_sp,
       SUM(i.Story_Point > 0) AS n_sp_positivo,
       ROUND(100 * SUM(i.Story_Point IS NOT NULL) / COUNT(*), 1) AS pct_com_sp
FROM Issue i JOIN Project p ON p.ID = i.Project_ID
WHERE i.Sprint_ID IS NOT NULL
GROUP BY p.Project_Key
ORDER BY pct_com_sp DESC;
