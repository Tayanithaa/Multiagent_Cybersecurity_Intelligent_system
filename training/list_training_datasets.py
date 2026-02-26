"""
List which training scripts use which dataset.
"""
import ast
import glob
import os


def extract_data_path(py_path):
    with open(py_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=py_path)

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CONFIG":
                    if isinstance(node.value, ast.Dict):
                        for key_node, value_node in zip(node.value.keys, node.value.values):
                            if isinstance(key_node, ast.Constant) and key_node.value == "data_path":
                                if isinstance(value_node, ast.Constant):
                                    return value_node.value
    return None


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    training_scripts = sorted(glob.glob(os.path.join(script_dir, "train_*_model.py")))

    print("Training script -> dataset")
    print("-" * 40)
    for script in training_scripts:
        data_path = extract_data_path(script) or "<not found>"
        print(f"{os.path.basename(script)} -> {data_path}")


if __name__ == "__main__":
    main()
