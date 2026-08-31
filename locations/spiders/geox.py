from typing import Any, AsyncIterator

import scrapy
from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature


class GeoxSpider(scrapy.Spider):
    name = "geox"
    item_attributes = {"brand": "Geox", "brand_wikidata": "Q588001"}

    async def start(self) -> AsyncIterator[Any]:
        for country in [
            "AT",
            "BE",
            "BG",
            "CA",
            "CH",
            "CN",
            "CZ",
            "DE",
            "ES",
            "FR",
            "GB",
            "GR",
            "HR",
            "HU",
            "IT",
            "LT",
            "LU",
            "LV",
            "NL",
            "PL",
            "PT",
            "RO",
            "RU",
        ]:
            yield scrapy.Request(
                url=f"https://www.geox.com/on/demandware.store/Sites-xcom-international-Site/en_GL/Stores-FindAjax?country={country}"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        html_data = Selector(text=response.json()["storesTilesHtml"])
        for location in html_data.xpath('.//*[@class="custom-infowindow"]'):
            item = Feature()
            item["branch"] = location.xpath('.//*[contains(@class,"sl-store-name")]//text()').get()
            item["addr_full"] = location.xpath('.//*[contains(@class,"sl-store-address")]//text()').get()
            item["phone"] = location.xpath('.//*[contains(@title,"Phone number")]//text()').get()
            item["website"] = item["ref"] = response.urljoin(
                location.xpath('.//*[contains(@href,"/int/storedetails/")]/@href').get()
            )
            item["lat"], item["lon"] = location.xpath(".//@data-loc").get().split(",")
            yield item
