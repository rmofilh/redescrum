-- Q3: ligações (estado final; Issue_Link não tem data) que partem das issues de itens_sprint.csv.
-- Issue_Key do alvo é usado para casar a ligação com o Change_Log (15_changelog_links.sql).
-- q3_issues é criada por src/artigo/extrair_q3.py a partir de itens_sprint.csv.
SELECT l.Issue_ID AS issue_id, l.Target_Issue_ID AS target_issue_id, l.Name AS nome,
       l.Description AS descricao, l.Direction AS direcao, t.Issue_Key AS target_key
FROM Issue_Link l
JOIN q3_issues q ON q.issue_id = l.Issue_ID
LEFT JOIN Issue t ON t.ID = l.Target_Issue_ID
ORDER BY l.Issue_ID, l.ID;
