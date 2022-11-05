import ast
import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser


class TrueValueSpider(SitemapSpider):
    name = "truevalue"
    item_attributes = {"brand": "True Value", "brand_wikidata": "Q7847545"}
    allowed_domains = ["stores.truevalue.com"]
    sitemap_urls = ["https://stores.truevalue.com/robots.txt"]
    sitemap_rules = [
        (r"stores\.truevalue\.com/.*/.*/.*/", "parse"),
    ]
    custom_settings = {
        "METAREFRESH_ENABLED": False,
    }

    def parse(self, response):
        script = response.xpath('//script[@type="application/ld+json"]/text()')[1].get()
        # json with // comments, trailing commas, etc.
        script = re.sub('//[^"]*$', "", script, flags=re.M)
        ld = ast.literal_eval(script[script.index("{") :])
        hours = ld.pop("openingHoursSpecification")
        item = LinkedDataParser.parse_ld(ld)
        oh = OpeningHours()
        oh.from_linked_data({"openingHoursSpecification": hours}, "%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
