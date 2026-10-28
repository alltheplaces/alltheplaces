import json
import re
from typing import AsyncIterator

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class CashExpressSpider(Spider):
    name = "cash_express"
    item_attributes = {"brand": "Cash Express", "brand_wikidata": "Q136374457", "name": "Cash Express"}
    allowed_domains = ["www.cashexpress.fr", "www.cashexpress.be"]

    async def start(self) -> AsyncIterator[Request]:
        # The French site also lists the Andorra and overseas stores
        for domain in self.allowed_domains:
            yield Request(f"https://{domain}/magasin/informations")

    def parse(self, response: Response):
        regions = json.loads(response.xpath('//div[contains(@class, "const-map-locations")]/@data-value').get())
        for stores in regions.values():
            for store in stores:
                yield Request(store["url"], callback=self.parse_store, cb_kwargs={"store": store})

    def parse_store(self, response: Response, store: dict):
        item = Feature()
        item["ref"] = store["id"]
        item["website"] = store["url"]
        item["lat"] = store["latitude"]
        item["lon"] = store["longitude"]
        item["country"] = store["country"]
        title = response.xpath('(//div[contains(@class, "shop__title")])[1]')
        item["branch"] = title.xpath("normalize-space(./text()[last()])").get()

        address = title.xpath("normalize-space(./following-sibling::div[1]/text())").get()
        if m := re.fullmatch(r"(.+) (AD\d{3}|\d{4,5}) (\D.*)", address, re.IGNORECASE):
            item["street_address"] = m.group(1).rstrip(",")
            item["postcode"], item["city"] = m.group(2).upper(), m.group(3)
        else:
            item["addr_full"] = address

        # The "buy" tab holds the shop opening hours, the "sell" tab the buyback counter hours
        oh = OpeningHours()
        valid = True
        for row in response.xpath('(//div[contains(@class, "shop-pickup__hours__list")])[1]/div'):
            day = sanitise_day(row.xpath("normalize-space(./div[1])").get(), DAYS_FR)
            ranges = []
            for time_range in row.xpath("./div[2]/text()").getall():
                if "Fermé" in time_range:
                    oh.set_closed(day)
                elif m := re.search(r"(\d\d:\d\d) - (\d\d:\d\d)", time_range):
                    ranges.append(m.groups())
                    oh.add_range(day, *m.groups())
            # A few stores publish overlapping ranges, e.g. "10:00 - 14:00" and "12:30 - 19:00"
            ranges.sort()
            if any(start < prev_end for (_, prev_end), (start, _) in zip(ranges, ranges[1:])):
                valid = False
        # Some stores show every day as closed, which is not a real schedule
        if valid and ":" in oh.as_opening_hours():
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
