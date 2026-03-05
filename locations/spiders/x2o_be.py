import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class X2oBESpider(Spider):
    name = "x2o_be"
    item_attributes = {"name": "X2O", "brand": "X2O", "brand_wikidata": "Q126165101"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.x2o.be/nl/showrooms.data",
            headers={"Accept": "text/x-component"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        slugs = sorted(set(re.findall(r"/showrooms/(x2o-badkamers-[a-z-]+)", response.text)))
        for slug in slugs:
            yield Request(
                url=f"https://www.x2o.be/nl/showrooms/{slug}",
                callback=self.parse_store,
                cb_kwargs={"slug": slug},
            )

    def parse_store(self, response: Response, slug: str, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = slug

        name = response.xpath("//h1/text()").get("")
        item["branch"] = name.removeprefix("X²O Badkamers ").removeprefix("X2O Badkamers ").strip()

        address_section = response.xpath('//h3[contains(text(), "Adres")]/following-sibling::div[1]')
        if address_section:
            item["street_address"] = address_section.xpath("p[1]/text()").get()
            city_text = address_section.xpath("p[2]//text()").getall()
            city_parts = "".join(city_text).split()
            if city_parts:
                item["postcode"] = city_parts[0]
                item["city"] = " ".join(city_parts[1:])

        phone = response.xpath(
            '//h3[contains(text(), "Telefoonnummer")]/following::a[starts-with(@href, "Tel:")]/@href'
        ).get()
        if phone:
            item["phone"] = phone.removeprefix("Tel: ")

        item["website"] = item["extras"]["website:nl"] = f"https://www.x2o.be/nl/showrooms/{slug}"
        item["extras"]["website:fr"] = f"https://www.x2o.be/fr/showrooms/{slug.replace('badkamers', 'salles-de-bain')}"

        item["opening_hours"] = self._parse_hours(response)

        apply_category(Categories.SHOP_BATHROOM_FURNISHING, item)

        yield item

    def _parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        rows = response.xpath('//h3[contains(text(), "Openingsuren")]/following-sibling::div[1]/div')
        for row in rows:
            day_name = row.xpath("p/text()").get("")
            day_en = sanitise_day(day_name, DAYS_NL)
            if not day_en:
                continue
            times = row.xpath(".//span/text()").getall()
            if len(times) == 2:
                oh.add_range(day_en, times[0], times[1])
        return oh
