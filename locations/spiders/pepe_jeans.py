from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

PEPE_JEANS = {"brand": "Pepe Jeans", "brand_wikidata": "Q426992"}


class PepeJeansSpider(Spider):
    name = "pepe_jeans"
    start_urls = ["https://www.pepejeans.com/intl/en/page/store-locator.html"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="store-card"]'):
            item = Feature()
            if name := location.xpath(".//h2/text()").get():
                if name.startswith("AWWG Outlet "):
                    item["name"] = "AWWG Outlet"
                    item["branch"] = name.removeprefix("AWWG Outlet ")
                elif name.startswith("Pepe Jeans Outlet Factory "):
                    item["name"] = "Pepe Jeans Outlet Factory"
                    item["branch"] = name or name.removeprefix("Pepe Jeans Outlet Factory ")
                    item.update(PEPE_JEANS)
                elif name.startswith("Pepe Jeans Outlet "):
                    item["name"] = "Pepe Jeans Outlet"
                    item["branch"] = name or name.removeprefix("Pepe Jeans Outlet ")
                    item.update(PEPE_JEANS)
                elif name.startswith("Pepe Jeans "):
                    item["name"] = "Pepe Jeans"
                    item["branch"] = name or name.removeprefix("Pepe Jeans ")
                    item.update(PEPE_JEANS)
                else:
                    item["name"] = name

            item["street_address"] = location.xpath(".//p/text()").get()
            item["addr_full"] = item["ref"] = merge_address_lines(
                [item["street_address"], location.xpath(".//p[2]/text()").get()]
            )
            item["phone"] = location.xpath('.//*[@class = "phone"]/text()').get()

            extract_google_position(item, location)
            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
