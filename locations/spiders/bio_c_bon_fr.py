import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class BioCBonFRSpider(Spider):
    name = "bio_c_bon_fr"
    item_attributes = {"brand_wikidata": "Q54312551"}
    allowed_domains = ["www.bio-c-bon.eu"]
    start_urls = ["https://www.bio-c-bon.eu/nos-magasins/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        # The store finder only links to regions, each region page lists its stores
        for url in response.xpath('//a[re:test(@href, "^/nos-magasins/[A-Z]{2}-[A-Z]+$")]/@href').getall():
            yield response.follow(url, self.parse_region)

    def parse_region(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for url in response.xpath('//a[starts-with(@href, "/magasin/")]/@href').getall():
            yield response.follow(url, self.parse_store)

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rsplit("/", 1)[1]
        item["website"] = response.url
        item["branch"] = (
            response.xpath('normalize-space(//div[@class="store__header__infos__title"])')
            .get()
            .removeprefix("Bio c' Bon")
            .strip()
        )
        address = response.xpath(
            '//div[@class="store-info"][div[@class="store-info__label"]="Adresse"]//p/text()'
        ).getall()
        address = [line.strip() for line in address if line.strip()]
        item["street_address"] = address[0]
        item["postcode"], item["city"] = address[-1].split(" ", 1)
        item["phone"] = response.xpath('//div[@class="store-info"]//a[starts-with(@href, "tel:")]/text()').get()

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//div[@class="store__header__infos__openingdays text-content"]/div'):
            day = DAYS_FR[rule.xpath('./span[@class="day"]/text()').get().strip(" :")]
            hours = rule.xpath('./span[@class="opening"]/text()').get("").strip()
            if hours == "Fermé":
                item["opening_hours"].set_closed(day)
            for open_time, close_time in re.findall(r"(\d{2}:\d{2}) - (\d{2}:\d{2})", hours):
                item["opening_hours"].add_range(day, open_time, close_time)

        yield item
