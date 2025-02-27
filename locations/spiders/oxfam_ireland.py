from typing import Any

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature


class OxfamIrelandSpider(Spider):
    name = "oxfam_ireland"
    item_attributes = {"brand": "Oxfam", "brand_wikidata": "Q267941"}
    start_urls = ["https://www.oxfamireland.org/shops"]

    recycle_types = {
        "accessories": None,
        "books": "recycling:books",
        "clothing": "recycling:clothes",
        "electricals": "recycling:electrical_appliances",
        "furniture": "recycling:furniture",
        "homewares": None,
        "music": None,
        "vintage": None,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//article[contains(@class, "location-card")]'):
            yield Request(
                response.urljoin(location.xpath(".//a/@href").get()),
                callback=self.parse_page,
                meta={
                    "lat": location.xpath('.//p[@class="latitude"]/text()').get(),
                    "lon": location.xpath('.//p[@class="longitude"]/text()').get(),
                },
            )

    def parse_page(self, response: Response, **kwargs: Any) -> Any:
        item = Feature(lat=response.meta["lat"], lon=response.meta["lon"])
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//*[contains(@class, "address")]/text()').get()
        name = response.xpath('//meta[@property="og:title"]/@content').get()
        item["email"] = response.xpath('//a[contains(@href, "mailto")]/text()').get()
        item["phone"] = response.xpath('//a[contains(@href, "tel")]/text()').get()

        if name.startswith("Oxfam Books "):
            item["name"] = "Oxfam Books"
        item["branch"] = name.removeprefix("Oxfam Books ")

        apply_category(Categories.SHOP_CHARITY, item)

        for label in response.xpath('//*[contains(@class, "shop-accepts-item-label")]/text()').getall():
            if tag := self.recycle_types.get(label.strip().lower()):
                apply_yes_no(tag, item, True)

        yield item
