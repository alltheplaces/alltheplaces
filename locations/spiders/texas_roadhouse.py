from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TexasRoadhouseSpider(SitemapSpider):
    name = "texas_roadhouse"
    item_attributes = {
        "brand": "Texas Roadhouse",
        "brand_wikidata": "Q7707945",
    }

    sitemap_urls = ["https://www.texasroadhouse.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/.*", "parse_store")]

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        for store_times in store_hours:
            if ":" in store_times:
                day, times = store_times.strip().split(" : ")
                open_time, close_time = times.split(" - ")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time.replace(" ", ""),
                    close_time=close_time.replace(" ", ""),
                    time_format="%I:%M%p",
                )
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        item = Feature()
        item["branch"] = response.xpath('//*[@class="vendor-block-content-top"]/h2/text()').get().strip()
        item["ref"] = item["branch"]
        item["addr_full"] = clean_address(response.xpath('//*[@class="store-address"]/text()').getall())
        item["phone"] = response.xpath('.//*[contains(@href, "tel")]/@href').get()
        item["opening_hours"] = self.parse_hours(response.xpath('//*[@class="open-dine-hours"]/ul/li/text()').getall())
        yield item
