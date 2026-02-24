import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class YesBRSpider(JSONBlobSpider):
    name = "yes_br"
    item_attributes = {"brand": "Yes! Idiomas", "brand_wikidata": "Q121365811"}
    start_urls = [
        "https://yes.com.br/site_novo/index.php?hcs=locatoraid&hca=search%3Asearch%2F%2Fproduct%2F",
    ]
    locations_key = "results"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature.get("address").replace("<br>\n", ",")
        if phone := feature.get("phone"):
            all_numbers = re.search(r">(.*)<", phone).group(1)
            if "/" in all_numbers:
                item["phone"] = all_numbers.split("/")[0].lstrip()
            else:
                item["phone"] = all_numbers.replace("Telefone ", "")
        item["website"] = feature.get("website_url")
        item["street_address"] = feature.get("street1")
        item["street"] = feature.get("street2")
        item["branch"] = item.pop("name").replace("YES! ", "")
        apply_category({"amenity": "language_school"}, item)
        yield item
