import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.buco_na_za import BucoNAZASpider
from locations.spiders.builders import BuildersSpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class TalismanHireSpider(WPStoreLocatorSpider):
    name = "talisman_hire"
    item_attributes = {"brand": "Talisman Hire", "brand_wikidata": "Q120885726"}
    allowed_domains = ["www.talisman.co.za"]
    drop_attributes = {"email", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = re.sub(r"\s*\(in(?:side)? .+?\)$", "", item.pop("name"))
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            "; ".join(
                f"{days}: {feature[key]}"
                for days, key in [("Mo-Fr", "hours_weekdays"), ("Sa", "hours_saturday"), ("Su", "hours_sunday")]
                if feature.get(key)
            )
        )

        if host := re.search(r"-in(?:side)?-(.+)$", item["website"].rstrip("/").rsplit("/", 1)[-1]):
            match host.group(1):
                case "builders":
                    item["located_in"] = BuildersSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = BuildersSpider.item_attributes["brand_wikidata"]
                case "builders-express":
                    item["located_in"] = "Builders Express"
                    item["located_in_wikidata"] = BuildersSpider.item_attributes["brand_wikidata"]
                case "buco":
                    item["located_in"] = BucoNAZASpider.item_attributes["brand"]
                    item["located_in_wikidata"] = BucoNAZASpider.item_attributes["brand_wikidata"]
                case _:
                    item["located_in"] = host.group(1).replace("-", " ").title()

        apply_category(Categories.SHOP_TOOL_HIRE, item)

        yield item
