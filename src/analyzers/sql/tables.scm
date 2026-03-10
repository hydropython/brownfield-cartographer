; Extract table references from SQL (FROM, JOIN clauses)
(select_statement
  from_clause: (from_clause
    (table_reference
      name: (identifier) @table_name))) @table_ref

(select_statement
  join_clause: (join_clause
    (table_reference
      name: (identifier) @table_name))) @table_ref