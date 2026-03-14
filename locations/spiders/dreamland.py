from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DreamlandSpider(Spider):
    name = "dreamland"
    item_attributes = {"brand_wikidata": "Q13574205"}
    start_urls = ["https://www.dreamland.nl/vestigingen", "https://www.dreamland.be/nl/winkels"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="overview-store"]'):
            item = Feature()
            item["ref"] = "{}-{}".format(
                response.url.split("/")[2].split(".")[2], location.xpath("@data-store-id").get()
            )
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["branch"] = (
                location.xpath('./h2[@class="overview-store__name"]/a/text()').get().removeprefix("DreamLand ")
            )
            item["website"] = response.urljoin(location.xpath('./h2[@class="overview-store__name"]/a/@href').get())
            item["street_address"] = location.xpath("./address/text()").get()
            item["addr_full"] = merge_address_lines(location.xpath("./address/text()").getall())

            apply_category(Categories.SHOP_TOYS, item)

            yield item
