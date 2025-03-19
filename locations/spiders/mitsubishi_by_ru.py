import chompjs
from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider
from locations.structured_data_spider import extract_phone


class MitsubishiBYRUSpider(JSONBlobSpider):
    name = "mitsubishi_by_ru"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.ru/for-byers/dealers/"]
    no_refs = True

    def extract_json(self, response: Response) -> list[dict]:
        return list(chompjs.parse_js_objects(response.xpath('//script[contains(text(), "placemarks")]/text()').get()))[
            -1
        ]

    def post_process_item(self, item, response, feature):
        extract_phone(item, Selector(text=feature["phone"]))
        item["website"] = (
            "https://www." + feature["www"].replace("www.", "")
            if not feature["www"].startswith("http")
            else feature["www"]
        )
        if "mitsubishi" not in item["website"]:  # Not a branded location
            return

        apply_category(Categories.SHOP_CAR, item)
        apply_yes_no(Extras.CAR_REPAIR, item, feature.get("service_partner") == "1")
        yield item
