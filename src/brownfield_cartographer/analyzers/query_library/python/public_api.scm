; Extract public functions (not starting with _)
(function_definition
  name: (identifier) @name
  (#not-match? @name "^_")) @public_function

; Extract public classes
(class_definition
  name: (identifier) @name
  (#not-match? @name "^_")) @public_class
