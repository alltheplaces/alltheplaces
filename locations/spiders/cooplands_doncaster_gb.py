from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CooplandsDoncasterGBSpider(scrapy.Spider):
    name = "cooplands_doncaster_gb"
    allowed_domains = ["cooplands.co.uk"]
    item_attributes = {"brand": "Cooplands", "brand_wikidata": "Q96622197"}
    start_urls = ["https://cooplands.co.uk/shop-locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.xpath("//div[@class='box box-store']")

        for index, store in enumerate(stores):
            data = store.xpath("ul/li/text()").extract()
            addr_full = merge_address_lines(data[:-1])

            item = Feature(
                ref=index,
                name="Cooplands",
                branch=store.xpath("h4/text()").extract_first(),
                addr_full=addr_full,
                postcode=data[-2].strip(),
                phone=data[-1].strip(),
            )
            apply_category(Categories.SHOP_BAKERY, item)
            yield item
