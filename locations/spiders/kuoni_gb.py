from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.john_lewis_gb import JohnLewisGBSpider
from locations.spiders.tesco_gb import set_located_in


class KuoniGBSpider(JSONBlobSpider):
    name = "kuoni_gb"
    item_attributes = {"brand": "Kuoni", "brand_wikidata": "Q684355"}
    start_urls = ["https://www.kuoni.co.uk/api/appointment/get-stores/"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["isPartner"] is False:
            item["branch"] = feature["baseName"]
            item["name"] = None

        if feature["isJohnLewis"] is True:
            set_located_in(JohnLewisGBSpider.item_attributes, item)

        item["website"] = response.urljoin(feature["link"])

        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)

        yield item
