import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FlunchFRSpider(CrawlSpider):
    name = "flunch_fr"
    item_attributes = {"brand": "Flunch", "brand_wikidata": "Q629326"}
    start_urls = ["https://www.flunch.fr/restaurant/tous-les-restaurants-flunch"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/restaurant/", restrict_xpaths='//*[@class="list-wrapper"]'),
            callback="parse",
        )
    ]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//*[@class="fiche__infos"]/h1/text()').get().replace("FLUNCH ", "").strip()
        item["addr_full"] = clean_address(response.xpath('//*[@class="adress"]/p').xpath("normalize-space()").get())
        item["phone"] = response.xpath('//*[@class="phone"]/span/text()').get()
        extract_google_position(item, response)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@class="fiche"]//li'):
            day = sanitise_day(day_time.xpath("./span[1]/text()").get(), DAYS_FR)
            time = day_time.xpath("./span[2]/text()").get()
            if time:
                for open_time, close_time in re.findall(r"(\d+:\d+)\s*-\s*(\d+:\d+)", time.replace("h", ":")):
                    item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        apply_category(Categories.RESTAURANT, item)
        yield item
