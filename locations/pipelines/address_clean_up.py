import re
from html import unescape
from typing import Any

from scrapy import Spider

from locations.items import Feature


def merge_address_lines(address_lines: list[Any]) -> str:
    """
    For the strings provided in a list of objects, combine the strings
    together in the order they are listed into a single address string.
    :param address_lines: ordered list of objects from which string objects
                          are extracted, and remaining objects ignored.
    :return: single address string where each address component is separated
             by a comma. An address component could be a house number, street
             name, town/city, postcode, etc.
    """
    address_line_strings = [x for x in address_lines if isinstance(x, str)]
    return ", ".join(filter(None, [line.strip() if line else None for line in address_line_strings]))


_multiple_spaces = re.compile(r" +")


def is_primarily_cjk(text: str) -> bool:
    """
    Check if more than half of `text` contains CJK (Chinese, Japanese, Korean) characters.
    """
    if not text:
        return False

    cjk_count = 0
    for char in text:
        if any(
            [
                "\u4e00" <= char <= "\u9fff",  # CJK Unified Ideographs
                "\u3040" <= char <= "\u309f",  # Hiragana
                "\u30a0" <= char <= "\u30ff",  # Katakana
                "\uac00" <= char <= "\ud7af",  # Hangul
            ]
        ):
            cjk_count += 1

    return cjk_count > len(text) / 2


def clean_address(address: list[Any] | str, min_length=2) -> str:
    if not address:
        return ""

    if isinstance(address, str):
        if address.strip().lower() in ("undefined", "n/a"):
            return ""

    if isinstance(address, list):
        address = merge_address_lines(address)

    address_list = (
        re.sub(_multiple_spaces, " ", unescape(address))
        .replace("\n", ",")
        .replace("\r", ",")
        .replace("\t", ",")
        .replace("\f", ",")
        .replace("<br>", ",")
        .replace("<br/>", ",")
        .replace("<br />", ",")
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

    # If after all of the cleaning our address is very short, its likely to be "-" or similar dud content.
    # Don't discard valid CJK characters, which may be short.
    if len(assembled_address) <= min_length and not is_primarily_cjk(assembled_address):
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
                if isinstance(value, str) or isinstance(value, list):
                    item[key] = clean_address(value, min_length)
        return item
