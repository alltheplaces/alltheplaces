from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature


class TalbotsSpider(CrawlSpider):
    name = "talbots"
    allowed_domains = ["www.talbots.com"]
    start_urls = ["https://www.talbots.com/view-all-stores/"]
    rules = [Rule(LinkExtractor(allow=r"store\?StoreID=(\d+)$"), callback="parse_each_website")]
    item_attributes = {"brand": "Talbots", "brand_wikidata": "Q7679064"}

    def parse_each_website(self, response):
        properties = {
            "ref": response.xpath('//input[@id="storeId"]/@value').get(),
            "website": response.url,
            "name": self.sanitize_name(response.xpath('//*[@id="storedetails-wrapper"]/h1/text()').get()),
            "phone": response.xpath('//*[@id="storePhone"]/a/text()').get(),
            "addr_full": self.get_address(response.xpath('//*[@id="storeAddress"]/div/div/div[1]/text()').getall()),
            "opening_hours": self.sanitize_time(response.xpath('//*[@id="storeHours"]/div/text()').getall()),
        }
        properties["lat"], properties["lon"] = response.xpath('//input[@id="address"]/@value').get().split(", ")
        yield Feature(**properties)

    def get_address(self, response):
        address = []
        for line in response:
            add = line.replace("\n", "")
            if len(add) == 0:
                continue
            if "Phone:" in line:
                break
            address.append(add)
        return ", ".join(address)

    def sanitize_time(self, response):
        opening_hours = OpeningHours()
        for time in response:
            if time in ("\n", "Hours:"):
                continue
            day, times = time.split(maxsplit=1)
            if "CLOSED" in times:
                continue
            open_time, close_time = times.strip().split(" - ")
            opening_hours.add_range(day[:2], open_time, close_time, time_format="%I:%M %p")
        return opening_hours.as_opening_hours()

    def sanitize_name(self, response):
        return response.replace("\n", "")
