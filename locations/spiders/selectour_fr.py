from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone


class SelectourFRSpider(CrawlSpider):
    name = "selectour_fr"
    item_attributes = {"brand": "Selectour", "brand_wikidata": "Q3478073"}
    start_urls = ["https://www.selectour.com/agence"]
    rules = [
        Rule(LinkExtractor(allow=r"/agence/[-\w]+(?:/[-\w]+)?/\d+$")),
        Rule(LinkExtractor(allow=r"/agence/[-\w]+/[-\w]+/[-\w]+/\d+$"), callback="parse"),
    ]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//div[@class='container']/h4[@class='title']/text()").get()
        item["addr_full"] = merge_address_lines(response.xpath("//address//text()").getall())
        item["lat"], item["lon"] = response.xpath("//div[@id='agencyMap']/@data-latlng").get(default=", ").split(", ")
        extract_phone(item, response)
        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//ul[contains(@class, "schedule-list")]/li'):
            day = rule.xpath('./span[@class="day-label"]/text()').get().strip(" :")
            day = sanitise_day(day, DAYS_FR)
            if not day:
                continue
            times_ranges = rule.xpath('./span[@class="day-opening"]/text()').get().split(" , ")
            for time in times_ranges:
                try:
                    start_time, end_time = time.split(" - ")
                    item["opening_hours"].add_range(day, start_time, end_time)
                except:
                    pass
        yield item
