import re
from html import unescape

from scrapy import Spider

from locations.items import Feature


def merge_address_lines(address_lines: [str]) -> str:
    return ", ".join(filter(None, [line.strip() if line else None for line in address_lines]))


_multiple_spaces = re.compile(r" +")


def clean_address(address: list[str] | str, min_length=2) -> str:
    if not address:
        return ""

    if isinstance(address, str):
        if address.strip().lower() == "undefined":
            return ""

    if isinstance(address, list):
        address = merge_address_lines(address)

    address_list = (
        re.sub(_multiple_spaces, " ", unescape(address))
        .replace("\n", ",")
        .replace("\r", ",")
        .replace("\t", ",")
        .replace("\f", ",")
        .split(",")
    )

    return_addr = []

    for line in address_list:
        if line:
            line = line.replace("\xa0", " ")
            line = line.strip("\n\r\t\f ,")
            if line:
                return_addr.append(line)
    assembled_address = ", ".join(return_addr)

    # If after all of the cleaning our address is very short, its likely to be "-" or similar dud content
    if len(assembled_address) <= min_length:
        return ""

    return assembled_address


class AddressCleanUpPipeline:
    def process_item(self, item: Feature, spider: Spider):
        targeted_fields = {
            "street": 2,
            "city": 2,
            "postcode": 2,
            "state": 1,
            "street_address": 2,
            "addr_full": 2,
        }

        for key, min_length in targeted_fields.items():
            if value := item.get(key):
                if isinstance(value, str):
                    item[key] = clean_address(value, min_length)
        return item
