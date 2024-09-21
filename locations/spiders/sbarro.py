from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class SbarroSpider(CrawlSpider, StructuredDataSpider):
    name = "sbarro"
    item_attributes = {"brand": "Sbarro", "brand_wikidata": "Q2589409"}
    allowed_domains = ["sbarro.com"]
    start_urls = ["https://sbarro.com/locations/?user_search=78749&radius=50000&count=5000"]
    rules = (
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="location-name "]', process_value=lambda store_url: store_url + '/'),
            follow=True,
            callback="parse_sd",
        ),
    )

    def post_process_item(self, item, response, ld_data):
        item["name"] = response.xpath('//*[@class="location-name "]/text()').extract_first()
        oh = OpeningHours()
        for day in response.xpath('//*[@id="location-content-details"]/meta[@itemprop="openingHours"]').getall():
            oh.add_ranges_from_string(day)
        item["opening_hours"] = oh
        yield item
