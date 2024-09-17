import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ErieInsuranceSpider(SitemapSpider):
    name = "erie_insurance"
    item_attributes = {
        "brand": "Erie Insurance",
        "brand_wikidata": "Q5388314",
        "country": "US",
    }
    allowed_domains = ["www.erieinsurance.com"]
    sitemap_urls = ["https://www.erieinsurance.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www.erieinsurance.com/agencies/.", "parse")]

    def parse(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').get())
        if data["@type"] == "InsuranceAgency":
            item = DictParser.parse(data)

            item["ref"] = response.url
            item["website"] = response.url

            try:
                hours_string = data["openingHours"]
                opening_hours = OpeningHours()
                for day_hours in hours_string.replace(" ", "").split(","):
                    if not day_hours:
                        continue
                    day = day_hours[:2]
                    open, close = day_hours[2:].split("-")
                    opening_hours.add_range(day, open, close)
                item["opening_hours"] = opening_hours.as_opening_hours()
            except:
                self.crawler.stats.inc_value("failed_to_parse_hours")

            yield item
