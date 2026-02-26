from typing import Any, Iterable

from scrapy.http import JsonRequest, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HornbachSpider(JSONBlobSpider):
    name = "hornbach"
    BRANDS = {
        "bodenhaus": {"name": "Bodenhaus", "brand": "Bodenhaus"},
        "hornbach": {"brand": "HORNBACH", "brand_wikidata": "Q685926"},
    }
    start_urls = [
        "https://www.bodenhaus.de",
        "https://www.hornbach.de",
        "https://www.hornbach.at",
        "https://www.hornbach.ch",
        "https://www.hornbach.lu",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if api_endpoint := response.xpath("//@endpoint").get():
            yield JsonRequest(url=api_endpoint.replace("/store?", "/stores?"), callback=self.parse_locations)

    def parse_locations(self, response: TextResponse) -> Any:
        yield from super().parse(response)

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("data"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("BODENHAUS ").removeprefix("HORNBACH ")
        if brand_info := self.BRANDS.get(feature["client"]):
            item.update(brand_info)
        if feature["client"] == "bodenhaus":
            apply_category(Categories.SHOP_FLOORING, item)
        yield item
