import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class LouMalnatisPizzeriaUSSpider(Spider):
    name = "lou_malnatis_pizzeria_us"
    item_attributes = {"brand": "Lou Malnati's Pizzeria", "brand_wikidata": "Q6685628"}
    start_urls = ["https://www.loumalnatis.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for region in response.xpath('//a[substring(@href, string-length(@href) - 10) = "/locations/"]/@href').getall():
            yield response.follow(region, callback=self.parse)
        for card in response.xpath(
            '//div[contains(@class, "kadence-column")][.//a[contains(@href, "maps/dir/")]]'
            '[not(descendant::div[contains(@class, "kadence-column")][.//a[contains(@href, "maps/dir/")]])]'
        ):
            directions = card.xpath('.//a[contains(@href, "maps/dir/")]/@href').get("")
            website = card.xpath('.//a[contains(@href, "loumalnatis.com")][not(contains(@href, "maps"))]/@href').get()
            if not website:
                continue
            if match := re.search(r"(-?\d{1,2}\.\d{4,}),(-?\d{1,3}\.\d{4,})", directions):
                yield Request(
                    url=website,
                    meta={"lat": match.group(1), "lon": match.group(2)},
                    callback=self.parse_location,
                )

    def parse_location(self, response: Response) -> Any:
        branch = response.xpath("//h1//text()").get("").strip()
        if "coming" in branch.lower():
            return
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["lat"] = response.meta["lat"]
        item["lon"] = response.meta["lon"]
        item["branch"] = re.sub(r"^Lou Malnati['\u2019]s\s*[-\u2013]\s*", "", branch)
        item["addr_full"] = response.xpath(
            '//span[contains(@class, "wp-block-kadence-advancedheading")]/text()'
        ).re_first(r".+, [A-Z]{2} \d{5}(?:-\d{4})?")
        item["phone"] = response.xpath('//span[@class="kb-adv-text-inner"]/text()').re_first(r"\(\d{3}\) \d{3}-\d{4}")
        item["opening_hours"] = OpeningHours()
        for row in response.xpath('(//table[@class="locations-hours-table"])[1]/tbody/tr'):
            item["opening_hours"].add_ranges_from_string(
                f'{row.xpath("td[1]/text()").get("")} {row.xpath("td[2]/text()").get("")}'
            )
        apply_category(Categories.RESTAURANT, item)
        yield item
