-- Q3: datas dos comentários das issues de data/interim/itens_sprint.csv (sem texto).
-- q3_issues é criada por src/artigo/extrair_q3.py a partir de itens_sprint.csv.
SELECT c.Issue_ID AS issue_id, c.Creation_Date AS data
FROM Comment c
JOIN q3_issues q ON q.issue_id = c.Issue_ID
ORDER BY c.Issue_ID, c.Creation_Date, c.ID;
