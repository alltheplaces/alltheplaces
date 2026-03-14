from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_PL, OpeningHours, sanitise_day
from locations.items import Feature


class CastoramaPLSpider(CrawlSpider):
    name = "castorama_pl"
    item_attributes = {"brand": "Castorama", "brand_wikidata": "Q966971"}
    start_urls = ["https://www.castorama.pl/informacje/sklepy"]
    rules = [Rule(LinkExtractor(allow=[r"/sklepy/[-\w]+.html$"]), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath("//address//text()").get()
        item["addr_full"] = ",".join(response.xpath("//address//text()").getall())
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.SHOP_HARDWARE, item)
        oh = OpeningHours()
        for day_time in response.xpath('//*[@data-testid="store-hours-table"]//dl//div'):
            day = sanitise_day(day_time.xpath(".//dt/text()").get(), DAYS_PL)
            time = day_time.xpath(".//dd").xpath("normalize-space()").get()
            if time == "Zamknięte":
                oh.set_closed(day)
            else:
                open_time, close_time = time.split(" - ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
        yield item
