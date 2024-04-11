import json

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class TargetAUSpider(CrawlSpider):
    name = "target_au"
    item_attributes = {"brand": "Target", "brand_wikidata": "Q7685854"}
    allowed_domains = ["target.com.au"]
    start_urls = ["https://www.target.com.au/store-finder"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//*[@class="store-states"]'), callback="parse_state")]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse_state(self, response):
        data = json.loads(response.xpath('//script[@id="store-json-data"]/text()').get())
        for row in data["locations"]:
            body = scrapy.Selector(text=row["content"])
            href = body.xpath("//@href").get()
            properties = {
                "ref": href.rsplit("/", 1)[-1],
                "name": row["name"],
                "lat": row["lat"],
                "lon": row["lng"],
                "street_address": merge_address_lines(body.xpath('//*[@itemprop="streetAddress"]//text()').getall()),
                "city": body.xpath('//*[@itemprop="addressLocality"]/text()').get(),
                "state": body.xpath('//*[@itemprop="addressRegion"]/text()').get(),
                "postcode": body.xpath('//*[@itemprop="postalCode"]/text()').get(),
                "phone": body.xpath("//p[last()-1]/text()").get(),
                "website": response.urljoin(href),
            }
            yield Feature(**properties)
