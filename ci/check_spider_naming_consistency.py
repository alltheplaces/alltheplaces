import ast
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Tuple

COUNTRYCODE_COMPONENTS = {
    "AE",
    "AL",
    "AO",
    "AR",
    "AT",
    "AU",
    "BE",
    "BG",
    "BH",
    "BO",
    "BR",
    "BW",
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
    "EC",
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
    "MU",
    "MW",
    "MX",
    "MY",
    "MZ",
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
    "US",
    "VN",
    "ZA",
    "ZM",
    "ZW",
}


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")

    # If the first component is a number, spell it out
    if components[0].isdigit():
        components[0] = number_to_text(int(components[0])).replace(" ", "")

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


def number_to_text(number: int) -> str:
    """
    Converts the digits of a number into English words.

    For example, 1 -> "one", 42 -> "Forty Two", 123 -> "One Hundred Twenty Three".

    :param number: The number to convert.
    :return: The English words representing the number.
    """
    ones = [
        "Zero",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
    ]
    teens = [
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
    ]
    tens = [
        "",
        "Ten",
        "Twenty",
        "Thirty",
        "Forty",
        "Fifty",
        "Sixty",
        "Seventy",
        "Eighty",
        "Ninety",
    ]

    if number < 10:
        return ones[number]

    if number < 20:
        return teens[number - 10]

    if number < 100:
        return tens[number // 10] + (ones[number % 10] if number % 10 else "")

    if number < 1000:
        return ones[number // 100] + "Hundred" + (number_to_text(number % 100) if number % 100 else "")

    return str(number)


def check_file(file_path: Path) -> Tuple[Path, List[str]]:
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

    return (file_path, errors)


def main():
    # Find all Python files in the spiders directory
    spider_root = os.path.join(os.path.dirname(__file__), "../locations/spiders")
    python_files = [f for f in os.listdir(spider_root) if f.endswith(".py")]

    # use multiprocessing map to check all files in parallel
    with ThreadPoolExecutor() as executor:
        all_errors = executor.map(check_file, [os.path.join(spider_root, file) for file in python_files])

    # map the files to a list of errors
    per_file_errors = dict((file, errors) for file, errors in all_errors)

    # If none of the files have errors, exit with a success code
    if not any(per_file_errors.values()):
        sys.stderr.write("No formatting errors found.\n")
        exit(0)

    sys.stderr.write("Formatting errors found:\n")
    for file, errors in per_file_errors.items():
        if not errors:
            continue

        sys.stderr.write(f"\nIn file {os.path.basename(file)}:\n")
        for error in errors:
            sys.stderr.write(f"  - {error}\n")
    exit(1)


if __name__ == "__main__":
    main()
