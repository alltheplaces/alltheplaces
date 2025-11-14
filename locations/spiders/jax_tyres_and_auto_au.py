import re
from typing import AsyncIterator

from scrapy import Request, Spider

from locations.hours import OpeningHours
from locations.items import Feature


class JaxTyresAndAutoAUSpider(Spider):
    name = "jax_tyres_and_auto_au"
    item_attributes = {"brand": "Jax Tyres & Auto", "brand_wikidata": "Q54010471"}
    allowed_domains = ["www.jaxtyres.com.au"]
    start_urls = ["https://www.jaxtyres.com.au/tyre-stores"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response):
        stores = response.xpath('//div[contains(@class, "pgFnSt-storeContainerSingleReg")]/a[not(@class)]')
        for store in stores:
            name = store.xpath("text()").get()
            url = "https://www.jaxtyres.com.au" + store.xpath("@href").get()
            yield Request(url=url, meta={"name": name})

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.meta["name"],
            "lat": response.xpath("//main/@data-lat").get(),
            "lon": response.xpath("//main/@data-lng").get(),
            "addr_full": " ".join(
                (" ".join(response.xpath('//p[contains(@class, "pgStLcSn-addressContent")]/text()').getall())).split()
            ),
            "phone": response.xpath('//a[contains(@class, "pgStLcSn-phoneNumber")]/@href').get(),
            "website": response.url,
        }
        properties["opening_hours"] = OpeningHours()
        day_names = response.xpath('//div[contains(@class, "pgStLcSn-openingHours")]/div[1]/p/text()').getall()
        hour_ranges = response.xpath('//div[contains(@class, "pgStLcSn-openingHours")]/div[2]/p/text()').getall()
        for day_name, hours in zip(day_names, hour_ranges):
            if m := re.match(r"(\d?\d:\d\d\s*[AP]M)\s*-\s*(\d?\d:\d\d\s*[AP]M)", hours):
                properties["opening_hours"].add_range(day_name, m.group(1), m.group(2), "%I:%M %p")
        yield Feature(**properties)
