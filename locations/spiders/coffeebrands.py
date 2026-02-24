import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class CoffeebrandsSpider(CrawlSpider):
    name = "coffeebrands"
    item_attributes = {"brand": "Coffeebrands", "brand_wikidata": "Q122956019"}
    start_urls = ["https://coffeebrands.gr/stores"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//*[@class="w3-container"]'), callback="parse"),
    ]
    countries = {"germany": "DE", "saudi-arabia": "SA"}
    no_refs = True

    def parse(self, response, **kwargs):
        for store in response.xpath('//*[@class="linehover w3-text-cbcyan3"]'):
            item = Feature()
            item["street_address"] = store.xpath("./td[1]/text()").get()
            location = response.url.split("/")[-1]
            if location in self.countries:
                item["country"] = self.countries.get(location)
            else:
                item["country"] = "GR"
                item["city"] = location.title()
            item["website"] = response.url
            if timing := re.match(r"(\d+:\d+)\s*-\s*(\d+:\d+)", store.xpath("./td[2]/text()").get()):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(days=DAYS, open_time=timing.group(1), close_time=timing.group(2))
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
