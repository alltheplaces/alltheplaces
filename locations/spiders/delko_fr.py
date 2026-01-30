from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DelkoFRSpider(CrawlSpider, StructuredDataSpider):
    name = "delko_fr"
    contacts = ["team.marketing@delko.com"]
    item_attributes = {"brand": "Delko", "brand_wikidata": "Q132021672"}
    start_urls = ["https://delko.fr/garage/"]
    rules = [Rule(LinkExtractor(r"/garage/delko/[^/]+/(\d+)$"), "parse")]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Delko ")

        item["email"] = response.xpath('//b[contains(text(), "@delko.fr")]/text()').get()
        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item

    def parse_opening_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        for rule in response.xpath('//div[@id="garage-horaires"]/div/div'):
            day = sanitise_day(rule.xpath("./p/b/text()").get(), DAYS_FR)
            times = rule.xpath("./p/text()").getall()
            for time in times:
                if time == "fermé":
                    oh.set_closed(day)
                else:
                    oh.add_range(day, *time.split(" - "), time_format="%Hh%M")
        return oh
