from typing import Any, AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class WestsideINSpider(Spider):
    name = "westside_in"
    item_attributes = {"brand": "Westside", "brand_wikidata": "Q2336948"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://customapp.trent-tata.com/api/custom/getstore-all?type=Westside&page=1",
            headers={"Referer": "https://www.westside.com/"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = Selector(text=response.json().get("data"))
        for store in data.xpath('//*[@class = "storedetails"]'):
            item = Feature()
            item["name"] = store.xpath("./h3/text()").get()
            item["addr_full"] = store.xpath(".//p/text()").get()
            item["phone"] = store.xpath(".//p[2]/text()").get()
            item["ref"] = item["website"] = store.xpath(".//a/@href").get().replace(" ", "")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item

        if next_page_url := data.xpath('//*[contains(@aria-label,"Next")]/@href').get():
            yield Request(
                url=next_page_url + "&type=Westside",
                headers={"Referer": "https://www.westside.com/"},
                callback=self.parse,
            )
