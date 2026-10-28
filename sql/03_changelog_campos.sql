-- P2.1: campos alterados (Field) por Change_Type.
SELECT Change_Type AS change_type, Field AS field, COUNT(*) AS n
FROM Change_Log
GROUP BY Change_Type, Field
ORDER BY Change_Type, n DESC;
