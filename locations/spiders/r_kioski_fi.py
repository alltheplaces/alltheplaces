from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_FI, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class RKioskiFISpider(CrawlSpider):
    name = "r_kioski_fi"
    item_attributes = {"brand": "R-kioski", "brand_wikidata": "Q1571400"}
    start_urls = ["https://www.r-kioski.fi/kioskit/"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//div[@role="main"]/*/p/a'), callback="parse")]

    def parse(self, response):
        item = Feature()
        item["name"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath('//*[@class="retailer-info--col left"]/p/text()[1]').get()
        item["postcode"], item["city"] = (
            response.xpath('//*[@class="retailer-info--col left"]/p/text()[2]').re_first(r"(\d+\ \w+)").split(" ")
        )
        item["phone"] = response.xpath('//*[@class="phone_number"]/text()').re_first(r"(\d+-?\d+)")
        item["website"] = item["ref"] = response.url
        item["lat"], item["lon"] = (
            response.xpath('//*[contains(@href, "maps")]/@href').re_first(r"(-?\d+\.\d+,-?\d+\.\d+)").split(",")
        )
        days = response.xpath('//*[@class="hours"]/preceding-sibling::h4/text()').getall()
        times = response.xpath('//*[@class="hours"]/text()').getall()
        item["opening_hours"] = self.parse_opening_hours(days, times)

        yield item

    def parse_opening_hours(self, days, times) -> OpeningHours:
        oh = OpeningHours()
        for day, time in zip(days, times):
            if time == "Suljettu":  # closed
                continue
            start_day, end_day = day.split("–") if "–" in day else [day, day]
            entry = day_range(sanitise_day(start_day, days=DAYS_FI), sanitise_day(end_day, days=DAYS_FI))
            start_time, end_time = time.split("–")

            oh.add_days_range(entry, start_time.strip(), end_time.strip())

        return oh
