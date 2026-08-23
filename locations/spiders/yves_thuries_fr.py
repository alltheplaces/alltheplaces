import re
from typing import AsyncIterator, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class YvesThuriesFRSpider(scrapy.Spider):
    name = "yves_thuries_fr"
    item_attributes = {"brand": "Yves Thuriès", "brand_wikidata": "Q141037098"}
    allowed_domains = ["yvesthuries.com"]

    async def start(self) -> AsyncIterator[scrapy.Request]:
        yield scrapy.FormRequest(
            url="https://yvesthuries.com/module/oh_storelocator/ajax",
            formdata={"ajax": "1", "action": "searchStores", "all": "1"},
            callback=self.parse,
        )

    def parse(self, response: Response) -> Iterable[scrapy.Request]:
        data = response.json()
        sel = scrapy.Selector(text=data.get("stores", ""))
        for article in sel.xpath('//article[contains(@class, "store-item")]'):
            url = article.xpath('.//a[contains(@class, "btn-outline-dark")]/@href').get()
            if not url:
                continue
            yield scrapy.Request(
                response.urljoin(url),
                callback=self.parse_store,
                cb_kwargs={
                    "lat": article.xpath("./@data-lat").get(),
                    "lon": article.xpath("./@data-lng").get(),
                    "ref": article.xpath("./@data-id").get(),
                },
            )

    def parse_store(self, response: Response, lat: str, lon: str, ref: str) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = ref
        item["lat"] = lat
        item["lon"] = lon
        item["website"] = response.url
        item["name"] = response.xpath('//h3[@class="title_name"]/text()').get("").strip()
        item["phone"] = response.xpath('//span[@itemprop="telephone"]//a/text()').get()
        item["email"] = response.xpath('//span[@itemprop="email"]//a/text()').get()

        address = " ".join(response.xpath('//address[@itemprop="address"]').xpath("string(.)").get("").split())
        if m := re.match(r"^(.*?)\s*(\d{5})\s+(.*)$", address):
            item["street_address"] = m.group(1)
            item["postcode"] = m.group(2)
            item["city"] = m.group(3)
        item["country"] = "FR"

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.SHOP_CHOCOLATE, item)

        yield item

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for day_row in response.xpath('//div[@class="hours"]//p[@class="day"]'):
            day_name = day_row.xpath('.//span[@class="dayname"]/text()').get("").strip()
            if day_name not in DAYS_FR:
                continue
            day = DAYS_FR[day_name]

            if day_row.xpath('.//span[@class="allday"]'):
                oh.set_closed(day)
                continue

            # Some store pages give one "halfday" span per full range (e.g.
            # "10h00-12h30"); others give one span per single time endpoint
            # (e.g. "09h00" then "19h00" as separate spans to be paired up).
            texts = [t.strip() for t in day_row.xpath('.//span[@class="halfday"]/text()').getall() if t.strip()]
            single_times = []
            for text in texts:
                if "-" in text:
                    open_time, _, close_time = text.partition("-")
                    single_times += [open_time, close_time]
                else:
                    single_times.append(text)

            for open_time, close_time in zip(single_times[0::2], single_times[1::2]):
                oh.add_range(day, self._to_hhmm(open_time), self._to_hhmm(close_time), "%H:%M")

        return oh

    @staticmethod
    def _to_hhmm(t: str) -> str:
        m = re.match(r"^\s*(\d{1,2})[hH:]?(\d{0,2})\s*$", t)
        hour, minute = m.group(1), m.group(2) or "00"
        return f"{int(hour):02d}:{int(minute):02d}"
