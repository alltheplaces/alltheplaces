import re

from scrapy.http import Response
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class SteigerStiftungAedSpider(CSVFeedSpider):
    name = "steiger_stiftung_aed"
    item_attributes = {
        "operator": "Steiger-Stiftung",
        "operator_wikidata": "Q879521",
        "nsi_id": "N/A",
    }
    start_urls = ["https://www.steiger-stiftung.de/download/page/maps/data/aeds.csv"]
    delimiter = "|"

    def parse_row(self, response: Response, row: dict) -> Feature:
        try:
            lat = float(row["lat"])
            lon = float(row["lng"])
        except (ValueError, TypeError):
            return

        if lat == 0.0 and lon == 0.0:
            return

        item = Feature()
        item["ref"] = row["AED"].strip()
        item["lat"] = lat
        item["lon"] = lon
        item["street_address"] = row["Straße"].strip() or None

        ort = row["Ort"].strip()
        if m := re.match(r"^(\d{5})\s+(.+)$", ort):
            item["postcode"] = m.group(1)
            item["city"] = m.group(2).strip()
        elif m := re.match(r"^(\d{4})\s+(.+)$", ort):
            item["postcode"] = m.group(1)
            item["city"] = m.group(2).strip()
        else:
            item["city"] = ort or None

        raw_name = row["Standortbeschreibung"].strip()
        clean_name = re.sub(r"<[^>]+>", " ", raw_name).strip()
        clean_name = re.sub(r"\s{2,}", " ", clean_name).strip()
        item["name"] = clean_name or None

        apply_category(Categories.DEFIBRILLATOR, item)
        yield item
