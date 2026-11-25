-- Q3: mudanças do campo assignee nas issues de data/interim/itens_sprint.csv.
-- q3_issues é criada por src/artigo/extrair_q3.py a partir de itens_sprint.csv.
SELECT c.Issue_ID AS issue_id, c.Creation_Date AS data, c.From_Value AS de, c.To_Value AS para
FROM Change_Log c
JOIN q3_issues q ON q.issue_id = c.Issue_ID
WHERE c.Field = 'assignee'
ORDER BY c.Issue_ID, c.Creation_Date, c.ID;
