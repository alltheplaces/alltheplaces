import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class MySizeAUSpider(CrawlSpider):
    name = "my_size_au"
    item_attributes = {"brand": "My Size", "brand_wikidata": "Q117948728"}
    allowed_domains = ["www.mysize.com.au"]
    start_urls = ["https://www.mysize.com.au/locations/"]
    rules = [Rule(LinkExtractor(allow=r"/locations/[\w\-]+"), callback="parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//div[@id="textContent"]/h2[1]//text()').get().strip().title(),
            "addr_full": re.sub(
                r"\s+",
                " ",
                " ".join(response.xpath('//div[@id="textContent"]/table[1]/tbody/tr[1]/td[1]/p[2]/text()').getall()),
            ).strip(),
            "phone": " ".join(
                response.xpath('//div[@id="textContent"]/table[1]/tbody/tr[1]/td[1]/p[3]/text()').getall()
            ).strip(),
            "website": response.url,
        }
        extract_google_position(properties, response)
        hours_string = " ".join(
            response.xpath('//div[@id="textContent"]/table[1]/tbody/tr[1]/td[2]/table[1]/tbody//text()').getall()
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
