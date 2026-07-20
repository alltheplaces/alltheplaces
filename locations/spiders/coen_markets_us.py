from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CoenMarketsUSSpider(Spider):
    name = "coen_markets_us"
    item_attributes = {"name": "Coen", "brand": "Coen Markets Inc", "brand_wikidata": "Q122856721"}
    allowed_domains = ["www.coenmarkets.com"]
    start_urls = ["https://www.coenmarkets.com/locations/?location_city=10000&zip_radius=10000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for marker in response.xpath(
            '//*[@class="location-archive-map"]//*[contains(@class, "acf-map-list-item acf-map-list-item")]'
        ):
            item = Feature()
            item["lat"] = marker.xpath('.//*[@class="location-lat"]/text()').get()
            item["lon"] = marker.xpath('.//*[@class="location-long"]/text()').get()
            item["ref"] = marker.xpath(".//@data-id").get()
            item["street_address"] = marker.xpath('.//p[contains(@class, "location-address")]/text()').get()
            item["addr_full"] = merge_address_lines(
                marker.xpath('.//p[contains(@class, "location-address")]/text()').getall()
            )
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
