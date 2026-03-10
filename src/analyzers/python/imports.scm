; Extract import statements from Python files
(import_statement
  name: (dotted_name) @import_path) @import_node

(import_from_statement
  module_name: (dotted_name) @import_path) @import_node

(import_from_statement
  module_name: (relative_import) @import_path) @import_node
