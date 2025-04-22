from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.flatgeobuf_spider import FlatGeobufSpider
from locations.items import Feature


class FrankstonCityCouncilBarbecuesAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_barbecues_au"
    item_attributes = {
        "operator": "Frankston City Council",
        "operator_wikidata": "Q132472668",
        "state": "VIC",
        "nsi_id": "N/A",
    }
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Recreation/Barbeque.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["Asset_ID"])
        apply_category(Categories.BARBECUE, item)
        match feature["Asset_SubType"]:
            case "Electric" | "Solar":
                apply_category({"fuel": "electric"}, item)
            case "Gas":
                apply_cateogry({"fuel": "gas"}, item)
            case _:
                pass
        yield item
