from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingFJSpider(CrawlSpider):
    name = "burger_king_fj"
    allowed_domains = ["www.burgerkingfiji.com"]
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.burgerkingfiji.com/locations/"]
    rules = [Rule(LinkExtractor(allow=r"/location/[-\w]+/?$"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = response.xpath('//*[@class="locationTopSection"]')
        item = Feature()
        item["ref"] = location.xpath('.//a[contains(@href, "maps")]/@href').get("").strip("/").split("/")[-1]
        item["website"] = response.url
        item["branch"] = location.xpath(".//h4/text()").get("").removeprefix("Burger King ")
        item["street"] = location.xpath(".//p/text()").get()
        item["opening_hours"] = self.parse_opening_hours(response)
        services = response.xpath('//h2[contains(text(), "Services")]/following-sibling::ul/p').get("")
        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.INDOOR_SEATING, item, "Dine-In" in services)
        apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in services)
        yield item

    def parse_opening_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for rule in response.xpath('//h2[contains(text(), "Store Hours")]/following-sibling::div[@class="row"]'):
            opening_hours = rule.xpath(".//p/text()").getall()
            for shift in opening_hours[1:]:
                if " - " in shift:
                    oh.add_range(opening_hours[0], *shift.split(" - "), "%I:%M%p")
        return oh
