from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_SE, DAYS_SE, OpeningHours
from locations.items import Feature


class Tele2SESpider(CrawlSpider):
    name = "tele2_se"
    item_attributes = {"brand": "Tele2", "brand_wikidata": "Q309865"}
    start_urls = ["https://www.tele2.se/butiker"]
    rules = [Rule(LinkExtractor(allow=r"/butiker/[a-z0-9\-]+$"), follow=False, callback="parse_store")]

    def parse_store(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//h1/text()").get()

        details = response.xpath('//div[@id="oppettider"]')
        item["addr_full"] = details.xpath('.//h2[text()="Besöksadress"]/following-sibling::span[1]/text()').get()

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            details.xpath('.//h2[text()="Öppettider"]/following::span[normalize-space(text())][1]/text()').get(),
            days=DAYS_SE,
            closed=CLOSED_SE,
        )

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item
