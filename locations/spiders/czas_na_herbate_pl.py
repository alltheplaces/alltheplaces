from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class CzasNaHerbatePLSpider(Spider):
    name = "czas_na_herbate_pl"
    item_attributes = {"brand": "Czas na Herbatę", "brand_wikidata": "Q123049012"}
    start_urls = [
        "https://czasnaherbate.net/nasze-sklepy/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="store-listing__list"]//li'):
            item = Feature()
            if location.xpath('.//*[@itemprop="name"]/text()').get():
                item["name"] = location.xpath('.//*[@itemprop="name"]/text()').get()
                item["street_address"] = item["ref"] = location.xpath('.//*[@itemprop="streetAddress"]//text()').get()
                item["lat"] = location.xpath(".//@data-lat").get()
                item["lon"] = location.xpath(".//@data-lng").get()
                item["phone"] = location.xpath(".//@data-phone").get()
                apply_category(Categories.SHOP_TEA, item)
                if location.xpath(".//@data-hours").get():
                    oh = OpeningHours()
                    oh.add_ranges_from_string(
                        location.xpath('.//*[@class="store-grid__hours-content"]').xpath("normalize-space()").get(),
                        days=DAYS_PL,
                    )
                    item["opening_hours"] = oh
                yield item
