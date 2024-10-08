import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class JohnLewisSpider(CrawlSpider):
    name = "john_lewis"
    item_attributes = {"brand": "John Lewis", "brand_wikidata": "Q1918981"}
    allowed_domains = ["www.johnlewis.com"]
    start_urls = ["https://www.johnlewis.com/our-shops"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/our-shops/[-\w]+", deny=["#", "international"]), follow=True, callback="parse_stores"
        )
    ]
    custom_settings = {"REDIRECT_ENABLED": False}
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse_stores(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url

        if location := json.loads(response.xpath('//script[@id="jsonPageData"]/text()').get()):
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")

        addr = response.xpath('//p[@class="shop-details-address"]/text()').get().replace("  ", " ")
        item["postcode"] = re.findall(r"[0-9A-Z]{2,4} {0,1}[0-9A-Z]{2,3}", addr)[-1]
        item["addr_full"] = f"{addr}, United Kingdom"

        item["name"] = response.xpath('//span[@class="shop-name"]/text()').get()
        item["phone"] = "+44 " + response.xpath('//span[@class="shop-details-telephone-number"]/text()').get()[1:]

        oh = OpeningHours()
        for day, hour in zip(response.xpath("//dt"), response.xpath("//dd")):
            if hour.xpath("./text()").get().strip() == "Closed":
                continue
            oh.add_range(
                day=day.xpath("./text()").get()[:3],
                open_time=hour.xpath("./text()").get().replace(".", ":").split(" - ")[0],
                close_time=hour.xpath("./text()").get().replace(".", ":").split(" - ")[1],
            )

        item["opening_hours"] = oh.as_opening_hours()

        yield item
