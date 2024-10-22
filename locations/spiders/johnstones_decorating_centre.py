from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature


class JohnstonesDecoratingCentreSpider(scrapy.Spider):
    name = "johnstones_decorating_centre"
    item_attributes = {"brand": "Johnstone's Decorating Centre", "brand_wikidata": "Q121742106"}
    start_urls = ["https://www.johnstonesdc.com/StoreLocator/AjaxStores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["markers"]:
            data = Selector(text=store["popupHTML"])
            item = Feature()
            item["branch"] = data.xpath("//h5/text()").get()
            item["street_address"] = data.xpath("//*[@class='address-holder']/text()").get()
            item["addr_full"] = data.xpath("//*[@class='address-holder']").xpath("normalize-space()").get()
            item["lat"], item["lon"] = store["location"]
            item["ref"] = store["id"]

            sel = Selector(text=store["card"])
            item["website"] = urljoin(
                "https://www.johnstonesdc.com", sel.xpath('//a[text() = "Shop detail"]/@href').get()
            )
            yield item
