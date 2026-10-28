# Esquema do TAWOS v1.1

Fonte: `TAWOS_Database_Schema_Creation_Script.sql` (https://github.com/SOLAR-group/TAWOS, branch `main`), copiado para `sql/00_TAWOS_Database_Schema_Creation_Script.sql`. Lista extraída **antes** da importação, conforme a Etapa 0.

## Divergências em relação ao roteiro (`docs/prompt_viabilidade_scrum.md`) e ao README do TAWOS

| Roteiro / README | Nome real no esquema | Consequência |
|---|---|---|
| `Sprint.Completion_Date` | `Sprint.Complete_Date` | só o nome muda |
| `Change_Log.ChangeType` | `Change_Log.Change_Type` | só o nome muda |
| "tabela de ligação Issue–Sprint" | **não existe**; `Issue.Sprint_ID` (FK única, N:1) | cada issue fica ligada a **uma só** Sprint; o histórico de *carry-over* precisa vir do `Change_Log` (campo `Sprint`) |
| `Change_Log` com valor anterior/novo | `From_Value`/`To_Value` (IDs) e `From_String`/`To_String` (texto) | para o campo Sprint, os valores são **listas** de IDs Jira (`Sprint.JiraID`), não `Sprint.ID` (verificado após a importação) |

## Tabelas e colunas

### `Repository`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Name` | varchar(512) |
| `Description` | varchar(2048) |
| `URL` | varchar(512) |

### `Project`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Project_Key` | varchar(128) |
| `Name` | varchar(512) |
| `URL` | varchar(512) |
| `Description` | varchar(2048) |
| `Start_Date` | datetime |
| `Last_Update_Date` | datetime |
| `Repository_ID` | int |

Chaves estrangeiras: `Repository_ID` → `Repository.ID`

### `User`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Project_ID` | int |

Chaves estrangeiras: `Project_ID` → `Project.ID`

### `Version`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Jira_ID` | int |
| `Name` | varchar(512) |
| `Description` | varchar(2048) |
| `Archived` | tinyint |
| `Released` | tinyint |
| `Release_Date` | datetime |
| `Project_ID` | int |

Chaves estrangeiras: `Project_ID` → `Project.ID`

### `Component`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Jira_ID` | int |
| `Name` | varchar(512) |
| `Description` | varchar(512) |
| `Project_ID` | int |

Chaves estrangeiras: `Project_ID` → `Project.ID`

### `Sprint`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `JiraID` | int |
| `Name` | varchar(512) |
| `State` | varchar(512) |
| `Start_Date` | datetime |
| `End_Date` | datetime |
| `Activated_Date` | datetime |
| `Complete_Date` | datetime |
| `Project_ID` | int |

Chaves estrangeiras: `Project_ID` → `Project.ID`

### `Issue`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Jira_ID` | int |
| `Issue_Key` | varchar(512) |
| `URL` | varchar(512) |
| `Title` | varchar(512) |
| `Description` | mediumtext |
| `Description_Text` | mediumtext |
| `Description_Code` | mediumtext |
| `Type` | varchar(128) |
| `Priority` | varchar(128) |
| `Status` | varchar(128) |
| `Resolution` | varchar(128) |
| `Creation_Date` | datetime |
| `Estimation_Date` | datetime |
| `Resolution_Date` | datetime |
| `Last_Updated` | datetime |
| `Story_Point` | double |
| `Timespent` | double |
| `In_Progress_Minutes` | double |
| `Total_Effort_Minutes` | double |
| `Resolution_Time_Minutes` | double |
| `Title_Changed_After_Estimation` | tinyint |
| `Description_Changed_After_Estimation` | tinyint |
| `Story_Point_Changed_After_Estimation` | tinyint |
| `Pull_Request_URL` | varchar(512) |
| `Creator_ID` | int |
| `Reporter_ID` | int |
| `Assignee_ID` | int |
| `Project_ID` | int |
| `Sprint_ID` | int |

Chaves estrangeiras: `Project_ID` → `Project.ID`; `Assignee_ID` → `User.ID`; `Reporter_ID` → `User.ID`; `Sprint_ID` → `Sprint.ID`; `Creator_ID` → `User.ID`

### `Comment`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Comment` | mediumtext |
| `Comment_Text` | mediumtext |
| `Comment_Code` | mediumtext |
| `Creation_Date` | datetime |
| `Author_ID` | int |
| `Issue_ID` | int |

Chaves estrangeiras: `Issue_ID` → `Issue.ID`; `Author_ID` → `User.ID`

### `Change_Log`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Field` | varchar(512) |
| `From_Value` | mediumtext |
| `To_Value` | mediumtext |
| `From_String` | mediumtext |
| `To_String` | mediumtext |
| `Change_Type` | varchar(512) |
| `Creation_Date` | datetime |
| `Author_ID` | int |
| `Issue_ID` | int |

Chaves estrangeiras: `Issue_ID` → `Issue.ID`; `Author_ID` → `User.ID`

### `Affected_Version`

| Coluna | Tipo |
|---|---|
| `Issue_ID` | int |
| `Affected_Version_ID` | int |

Chaves estrangeiras: `Issue_ID` → `Issue.ID`; `Affected_Version_ID` → `Version.ID`

### `Fix_Version`

| Coluna | Tipo |
|---|---|
| `Issue_ID` | int |
| `Fix_Version_ID` | int |

Chaves estrangeiras: `Issue_ID` → `Issue.ID`; `Fix_Version_ID` → `Version.ID`

### `Issue_Component`

| Coluna | Tipo |
|---|---|
| `Issue_ID` | int |
| `Component_ID` | int |

Chaves estrangeiras: `Component_ID` → `Component.ID`; `Issue_ID` → `Issue.ID`

### `Issue_Link`

| Coluna | Tipo |
|---|---|
| `ID` | int |
| `Issue_ID` | int |
| `Name` | varchar(512) |
| `Description` | varchar(2048) |
| `Direction` | varchar(45) |
| `Target_Issue_ID` | int |

Chaves estrangeiras: `Target_Issue_ID` → `Issue.ID`; `Issue_ID` → `Issue.ID`

## Verificação após a importação (`information_schema` do banco importado)

O DDL do dump (gerado por `mysqldump 8.0.30` a partir de um servidor 8.0.21, banco de origem `tawos_cleaned`) coincide com o script do GitHub, com **uma diferença**: `Project` tem uma coluna a mais, `SP_Field_ID` (ID do campo de story points no Jira de cada projeto), entre `Last_Update_Date` e `Repository_ID`.

| Tabela | Linhas |
|---|---:|
| Repository | 12 |
| Project | 39 |
| Sprint | 4.594 |
| Issue | 458.232 |
| Change_Log | 9.253.419 |
| Comment | 1.518.327 |
| Issue_Link | 246.587 |
| User | 206.162 |

Fatos sobre chaves verificados nos dados:

- `Sprint.JiraID` **não** é único globalmente (1.002 repetições) nem por repositório (273), mas é único por `(Project_ID, JiraID)`: uma mesma Sprint do Jira que contém issues de vários projetos foi gravada uma vez por projeto. O mapeamento usado é `(Issue.Project_ID, JiraID) → Sprint.ID`.
- `Change_Log.Field = 'Sprint'` (174.915 linhas, `Change_Type = 'OTHER'`): `From_Value`/`To_Value` são listas separadas por vírgula, por exemplo `'2278'` → `'2278, 2296'`, e `From_String`/`To_String` trazem os nomes das Sprints.
- Os status vêm com variações de caixa e espaços (`Resolved`/`RESOLVED`, `In Review`/`In  Review`); o código normaliza os nomes antes de comparar.
- `SERVER`, `DNN` e `EVG` não têm nenhuma linha em `Sprint`.
