-- Q3: criação/remoção de ligações (Field = 'Link') nas issues de data/interim/itens_sprint.csv.
-- Issue_Link não tem data; o Change_Log da issue de origem data cada ligação:
-- adição -> To_Value = chave da issue alvo; remoção -> From_Value = chave da issue alvo.
-- q3_issues é criada por src/artigo/extrair_q3.py a partir de itens_sprint.csv.
SELECT c.Issue_ID AS issue_id, c.Creation_Date AS data, c.From_Value AS de, c.To_Value AS para,
       c.From_String AS de_texto, c.To_String AS para_texto
FROM Change_Log c
JOIN q3_issues q ON q.issue_id = c.Issue_ID
WHERE c.Field = 'Link'
ORDER BY c.Issue_ID, c.Creation_Date, c.ID;
