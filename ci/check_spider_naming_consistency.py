import ast
import os
import re
from typing import List

ALLOWED_UPPERCASE_COMPONENTS = {
    "AU",
    "AT",
    "BE",
    "BG",
    "CA",
    "CZ",
    "CH",
    "DE",
    "DK",
    "ES",
    "FR",
    "GB",
    "HU",
    "IE",
    "IN",
    "IT",
    "KE",
    "KW",
    "KR",
    "KZ",
    "MT",
    "MX",
    "NL",
    "NO",
    "NZ",
    "PL",
    "PT",
    "RO",
    "RS",
    "RU",
    "SE",
    "TR",
    "TW",
    "US",
    "UK",
    "ZA",
}


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")

    # Allow some special cases to be all caps
    for i, component in enumerate(components):
        if component.upper() in ALLOWED_UPPERCASE_COMPONENTS:
            components[i] = component.upper()
        else:
            components[i] = component.title()

    return "".join(components)


def camel_to_snake(camel_str: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()


def check_file(file_path: str) -> List[str]:
    errors = []
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    # Open the file and parse it into a Python AST
    with open(file_path, "r") as file:
        tree = ast.parse(file.read())

    # Walk the AST and look for class definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            spider_name = None

            # Look for an assignment to the spider_name variable
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "name":
                            spider_name = item.value.s
                            break
                    if spider_name:
                        break

            if spider_name:
                expected_class_name = snake_to_camel(spider_name) + "Spider"
                expected_file_name = spider_name

                if class_name != expected_class_name:
                    errors.append(
                        f"Spider name '{spider_name}' should use class name '{expected_class_name}' instead "
                        f"of '{class_name}'"
                    )

                if file_name != expected_file_name:
                    errors.append(
                        f"Class name '{class_name}' should use file name '{expected_file_name}.py' instead "
                        f"of '{file_name}.py'"
                    )

    return errors


def main():
    # Find all Python files in the spiders directory
    spider_root = os.path.join(os.path.dirname(__file__), "../locations/spiders")
    python_files = [f for f in os.listdir(spider_root) if f.endswith(".py")]
    all_errors = []

    for file in python_files:
        errors = check_file(os.path.join(spider_root, file))
        if errors:
            all_errors.append((file, errors))

    if not all_errors:
        print("No formatting errors found.")
        exit(0)

    print("Formatting errors found:")
    for file, errors in all_errors:
        print(f"\nIn file {file}:")
        for error in errors:
            print(f"  - {error}")
    exit(1)


if __name__ == "__main__":
    main()
