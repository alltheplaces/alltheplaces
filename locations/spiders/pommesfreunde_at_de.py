import json
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PommesfreundeATDESpider(Spider):
    name = "pommesfreunde_at_de"
    item_attributes = {"brand": "Pommesfreunde", "brand_wikidata": "Q117083946"}
    start_urls = ["https://pommesfreunde.de/wp-json/wp/v2/lieferservice?per_page=100&_fields=id,title,link"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        stores = {store["id"]: store for store in response.json()}
        yield Request("https://pommesfreunde.de/standorte", callback=self.parse_markers, meta={"stores": stores})

    def parse_markers(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        markers = json.loads(response.xpath("//@data-markers").get())
        for marker in markers:
            if not (store := response.meta["stores"].get(marker["id"])):
                continue
            item = Feature()
            item["ref"] = str(marker["id"])
            item["lat"] = marker["latLang"]["lat"]
            item["lon"] = marker["latLang"]["lng"]
            item["branch"] = store["title"]["rendered"]
            item["website"] = store["link"]
            apply_category(Categories.FAST_FOOD, item)
            yield item
