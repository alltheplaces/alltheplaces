import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BitstopPRUSSpider(JSONBlobSpider):
    name = "bitstop_pr_us"
    allowed_domains = ["locus.bitstop.co"]
    start_urls = ["https://locus.bitstop.co:42010/api/current-locations"]
    operators = {
        "ATM Ops Inc": {
            "operator": "ATM Ops Inc",
            "operator_wikidata": "Q135316538",
            "brand": "Bitstop",
            "brand_wikidata": "Q135316538",
        },
        "CoinGenie": {
            "operator": "CoinGenie",
            "operator_wikidata": "Q135317411",
            "brand": "CoinGenie",
            "brand_wikidata": "Q135317411",
        },
        "Dynamic Exchange": {"operator": "Dynamic Exchange", "brand": "Dynamic Exchange"},
        "Express BTM": {
            "operator": "Express BTM",
            "operator_wikidata": "Q135316892",
            "brand": "Express BTM",
            "brand_wikidata": "Q135316892",
        },
        "PAI": {"operator": "PAI", "brand": "PAI"},
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0], method="POST")

    def extract_json(self, response: Response) -> list[dict]:
        # Keys of feature properties are remapped to codes to reduce the size
        # of the source JSON file. The original JSON file needs to be rebuilt.
        json_data = response.json()
        key_map = {code: key_name for key_name, code in json_data["data"]["keys"].items()}
        source_features = json_data["data"]["features"]["features"]
        rebuilt_features = []
        for source_feature in source_features:
            rebuilt_feature = {}
            rebuilt_feature["geometry"] = source_feature["geometry"]
            for property_code, property_value in source_feature["properties"].items():
                rebuilt_feature[key_map[property_code]] = property_value
            rebuilt_features.append(rebuilt_feature)
        return rebuilt_features

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("closing_date") or not feature.get("visible"):
            return

        item["ref"] = feature["atm_id"]
        item.pop("name", None)
        item["addr_full"] = item["addr_full"].removeprefix("Bitstop Bitcoin ATM, ")
        item["street_address"] = feature["address_line_1_2"]
        item["state"] = feature["administrative_area"]
        item["country"] = feature["country_region"]
        item.pop("phone", None)

        if located_in := feature.get("enclosing_location"):
            item["located_in"] = located_in

        if operator_name := feature.get("operator"):
            if operator_name in self.operators.keys():
                item["operator"] = self.operators[operator_name]["operator"]
                if operator_wikidata := self.operators[operator_name].get("operator_wikidata"):
                    item["operator_wikidata"] = operator_wikidata
                item["brand"] = self.operators[operator_name]["brand"]
                if brand_wikidata := self.operators[operator_name].get("brand_wikidata"):
                    item["brand_wikidata"] = brand_wikidata
            else:
                self.logger.warning(
                    "Unknown partner brand/operator '{}'. Feature still extracted but the spider needs updating with awareness of this partner brand/operator.".format(
                        operator_name
                    )
                )

        if photo_list := feature.get("other_photos"):
            photo_urls = photo_list.split(", ")
            for photo_url in photo_urls:
                if photo_url != "https://media.bitstop.co/media/bitstop-locations.jpg":
                    item["image"] = photo_url
                    break

        if hours_array := feature.get("working_hours_24"):
            item["opening_hours"] = OpeningHours()
            for day_hours in hours_array:
                for interval in day_hours[1]:
                    # Fix broken intervals
                    interval = interval.replace("060:00", "06:00").replace("00:00-01:00-", "")
                    # Merge split intervals that occur across midnight
                    interval = re.sub(r"^00:00-((?:0[0-9]|11):\d{2})-(\d{2}:\d{2})-24:00$", r"\2-\1", interval)
                    if interval.startswith("00:00-01:00-") and interval.endswith("-24:00"):
                        interval = interval.removeprefix("00:00-01:00-")
                    item["opening_hours"].add_range(
                        day_hours[0].replace("_hours", ""), *interval.split("-", 1), "%H:%M"
                    )

        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"

        item["extras"]["ref:google:place_id"] = feature["place_id"]
        if start_date := feature.get("location_opening_date"):
            item["extras"]["start_date"] = start_date

        yield item
