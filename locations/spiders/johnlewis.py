import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from scrapy.spiders import SitemapSpider


class JohnLewisSpider(SitemapSpider):
    name = "johnlewis"
    item_attributes = {"brand": "John Lewis", "brand_wikidata": "Q1918981"}
    allowed_domains = ["www.johnlewis.com"]
    sitemap_urls = ["https://www.johnlewis.com/shops-services.xml"]
    sitemap_rules = [
        (r"https:\/\/www\.johnlewis\.com\/our\-shops\/([-\w]+)", "parse_stores")
    ]
    custom_settings = {
        "REDIRECT_ENABLED": False,
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0",
    }

    def parse_stores(self, response):
        item = GeojsonPointItem()
        item["ref"] = response.url
        item["website"] = response.url

        location = json.loads(
            response.xpath('//script[@id="jsonPageData"]/text()').get()
        )
        if location:
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]

        addr_full = (
            response.xpath('//p[@class="shop-details-address"]/text()')
            .get()
            .replace("  ", " ")
        )
        postcode_re = re.match(r"([: \w]+) (\w{1,2}\d{1,2}\w? \d\w{2})", addr_full)
        if postcode_re:
            item["postcode"] = postcode_re.group(2)
            addr_full = ", ".join(
                [postcode_re.group(1), postcode_re.group(2), "United Kingdom"]
            )

        item["addr_full"] = addr_full

        item["name"] = response.xpath('//span[@class="shop-name"]/text()').get()
        item["phone"] = (
            "+44 "
            + response.xpath(
                '//span[@class="shop-details-telephone-number"]/text()'
            ).get()[1:]
        )

        opening_rules = response.xpath(
            '//dl[@class="opening-weeks-list"]/descendant::*/text()'
        ).getall()
        if opening_rules and len(opening_rules) == 14:
            oh = OpeningHours()
            for i in range(0, 7):
                day = opening_rules[i * 2][0:2]
                time = re.match(
                    r"(\d{2}:\d{2}) - (\d{2}:\d{2})",
                    opening_rules[(i * 2) + 1].replace(".", ":"),
                )
                oh.add_range(day, time.group(1), time.group(2))

            item["opening_hours"] = oh.as_opening_hours()

        yield item
