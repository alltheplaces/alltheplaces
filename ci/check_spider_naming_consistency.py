import ast
import os
import re
from typing import List

COUNTRYCODE_COMPONENTS = {
    "AE",
    "AL",
    "AR",
    "AT",
    "AU",
    "BE",
    "BG",
    "BH",
    "BO",
    "BR",
    "BY",
    "CA",
    "CH",
    "CL",
    "CN",
    "CY",
    "CZ",
    "DE",
    "DK",
    "DO",
    "EE",
    "EG",
    "ES",
    "EU",
    "FI",
    "FJ",
    "FR",
    "GB",
    "GG",
    "GR",
    "GT",
    "HK",
    "HR",
    "HU",
    "ID",
    "IE",
    "IL",
    "IM",
    "IN",
    "IT",
    "JE",
    "JP",
    "KE",
    "KR",
    "KW",
    "KZ",
    "LT",
    "LU",
    "LV",
    "MA",
    "ME",
    "MK",
    "MO",
    "MT",
    "MX",
    "MY",
    "NI",
    "NL",
    "NO",
    "NZ",
    "OM",
    "PE",
    "PH",
    "PK",
    "PL",
    "PR",
    "PT",
    "QA",
    "RO",
    "RS",
    "RU",
    "SA",
    "SE",
    "SG",
    "SI",
    "SK",
    "TH",
    "TR",
    "TW",
    "UA",
    "UK",
    "US",
    "VN",
    "ZA",
    "ZM",
    "ZW",
}


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")

    # Capitalize the first letter of each component except the first one
    for i, component in enumerate(components):
        components[i] = component.capitalize()

    # Allow consecutive country codes at the end of the spider name
    for i in range(len(components) - 1, 0, -1):
        if components[i].upper() not in COUNTRYCODE_COMPONENTS:
            break

        components[i] = components[i].upper()

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
                            spider_name = item.value.value
                            break
                    if spider_name:
                        break

            if spider_name:
                # Spider names should be lowercase or digits and only use underscores.
                if not re.match(r"^[a-z0-9_]+$", spider_name):
                    errors.append(
                        f"Spider name '{spider_name}' should only use lowercase letters/digits and underscores"
                    )

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
