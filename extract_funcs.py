
import ast

filename = "temp_old_server.py"
target_funcs = ["docx_batch_replace_text", "docx_copy_elements_range", "docx_get_element_source"]

with open(filename, "r") as f:
    source = f.read()

tree = ast.parse(source)

for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
        print(f"### {node.name} ###")
        print(ast.get_source_segment(source, node))
        print("\n")
