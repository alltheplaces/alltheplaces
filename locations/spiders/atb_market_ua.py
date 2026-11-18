from typing import Any, AsyncIterator

from scrapy import Request, Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class AtbMarketUASpider(Spider):
    name = "atb_market_ua"
    item_attributes = {"brand": "АТБ-Маркет", "brand_wikidata": "Q4054103"}
    allowed_domains = ["www.atbmarket.com"]

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.atbmarket.com/store-map")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city in response.xpath('//select[@id="stores-city"]/option[@value!=""]'):
            yield JsonRequest(
                f"https://www.atbmarket.com/site/getstoreattr?city={city.xpath('@value').get()}&generator=0&help_point=0&scan_buy=0&store_number=",
                callback=self.parse_stores,
                cb_kwargs={"city": city.xpath("normalize-space(text())").get()},
            )

    def parse_stores(self, response: Response, city: str) -> Any:
        coordinates = {str(c["id"]): c for c in response.json()["coordinates"]}
        for store in Selector(text=response.json()["optselect"]).xpath('//option[@value!=""]'):
            item = Feature()
            item["ref"] = store.xpath("@value").get()
            item["street_address"] = store.xpath("text()").get()
            item["city"] = city
            item["lat"] = coordinates[item["ref"]]["lat"]
            item["lon"] = coordinates[item["ref"]]["lng"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string("Mo-Su " + store.xpath("@worktime").get())
            apply_yes_no(Extras.BACKUP_GENERATOR, item, "з генератором" in store.xpath("@groupstring").get())
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
