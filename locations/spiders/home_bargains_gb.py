from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class HomeBargainsGBSpider(CrawlSpider, StructuredDataSpider):
    name = "home_bargains_gb"
    item_attributes = {"brand": "Home Bargains", "brand_wikidata": "Q5888229"}
    allowed_domains = ["storelocator.home.bargains"]
    start_urls = ["https://storelocator.home.bargains/all-stores"]
    rules = [Rule(LinkExtractor(allow="/store/"), callback="parse_sd", follow=False)]
    wanted_types = ["LocalBusiness"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_delay = 0.5

    def inspect_item(self, item, response):
        item["ref"] = response.url.split("/store/", 1)[1].split("/", 1)[0]
        full_address_parts = response.xpath('//*[@itemprop="address"]/text()').extract()[:-1]
        item["addr_full"] = clean_address(full_address_parts)
        item["postcode"] = full_address_parts[-1].strip()
        item["opening_hours"] = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@datetime').extract())
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/text()').extract_first()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/text()').extract_first()
        item["country"] = "GB"
        yield item

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            d, h = hour.split()
            day = d.capitalize()
            open_time, close_time = h.split("-")

            if open_time == "closed":
                pass
            else:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()
