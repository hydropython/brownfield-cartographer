; Extract class definitions with inheritance
(class_definition
  name: (identifier) @class_name
  superclasses: (argument_list
    (identifier) @base_class)?) @class_def
