import csv
import json
import logging
import pprint
import re

import requests
from scrapy import Selector

from locations.user_agents import BOT_USER_AGENT_REQUESTS


def main():
    mapping = parse_wiki()

    # Inherit tags when not documented on the wiki
    taxonomy = parse_taxonomy()
    for key, value in mapping.items():
        if value:
            continue
        for parent in taxonomy[key]:
            if inherited := mapping.get(parent):
                mapping[key] = inherited
                break

    with open("overture2osm.json", mode="w") as f:
        json.dump(mapping, f, sort_keys=True, indent="\t")
    pprint.pp(mapping)


def parse_wiki() -> dict:
    table = {}
    data = requests.get(
        "https://wiki.openstreetmap.org/w/api.php",
        {"action": "parse", "page": "Overture_Categories", "format": "json"},
        headers={"User-Agent": BOT_USER_AGENT_REQUESTS},
    ).json()
    page_html = Selector(text=data["parse"]["text"]["*"])
    for row in page_html.xpath('//table[@id="mapping_table"]//tr')[1:]:
        items = row.xpath("./td")
        if len(items) != 2:
            logging.warning(f"Unexpected row length: {row}")
            continue
        overture_value = items[0].xpath("./text()").get()
        table[overture_value] = {}
        if osm_tags := items[1].xpath("./code/text()").get():
            table[overture_value] = parse_tags(osm_tags)

    return table


def parse_tags(wiki_str: str) -> dict:
    tags = {}
    for tag in wiki_str.split(" and "):
        if m := re.match(r"^\s*([-_:\w]+)=([-_:\w]+)\s*$", tag):
            tags[m.group(1)] = m.group(2)
        else:
            logging.error(f"Failed to parse '{tag}' from '{wiki_str}'")

    return tags


def parse_taxonomy() -> dict:
    table = {}
    f = requests.get(
        "https://github.com/OvertureMaps/schema/raw/main/task-force-docs/places/overture_categories.csv",
    ).content.decode("utf-8-sig")
    for row in csv.DictReader(f.splitlines(), delimiter=";"):
        table[row["Category code"]] = []
        for parent in row["Overture Taxonomy"][1:-1].split(",")[:-1]:
            table[row["Category code"]].append(parent)
        table[row["Category code"]].reverse()
    return table


if __name__ == "__main__":
    main()
