import re
from html import unescape

from scrapy import Spider

from locations.items import Feature


def merge_address_lines(address_lines: [str]) -> str:
    return ", ".join(filter(None, [line.strip() if line else None for line in address_lines]))


_multiple_spaces = re.compile(r" +")


def clean_address(address: list[str] | str) -> str:
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

    return ", ".join(return_addr)


class AddressCleanUpPipeline:
    def process_item(self, item: Feature, spider: Spider):
        if street_address := item.get("street_address"):
            if isinstance(street_address, str):
                item["street_address"] = clean_address(street_address)
        if addr_full := item.get("addr_full"):
            if isinstance(addr_full, str):
                item["addr_full"] = clean_address(addr_full)
        return item
