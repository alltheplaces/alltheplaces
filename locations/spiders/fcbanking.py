import json
import re
import urllib.parse

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser


class FcbankingSpider(SitemapSpider):
    name = "fcbanking"
    item_attributes = {"brand": "First Commonwealth Bank", "brand_wikidata": "Q5452773"}
    allowed_domains = ["www.fcbanking.com"]
    sitemap_urls = ["https://www.fcbanking.com/robots.txt"]
    sitemap_follow = ["branch-locations"]
    sitemap_rules = [(r"branch-locations/.", "parse")]

    def parse(self, response):
        map_script = response.xpath('//script/text()[contains(., "setLat")]').get()
        map_script = map_script.replace("\r", "\n")
        lat = re.search(r'setLat\("(.*)"\)', map_script)[1]
        lon = re.search(r'setLon\("(.*)"\)', map_script)[1]

        ldjson = response.xpath('//script[@type="application/ld+json"]/text()').get()
        ldjson = ldjson.replace("\r", "\n")
        data = json.loads(re.sub(r"^//.*$", "", ldjson, flags=re.M))
        item = LinkedDataParser.parse_ld(data)
        item["lat"] = lat
        item["lon"] = lon
        item["website"] = response.url
        path = urllib.parse.urlsplit(response.url).path
        item["ref"] = path.removeprefix("/branch-locations")
        hours_fixed = [re.sub(r"([ap])\.m\.?", r"\1m", row).replace("\u2013", "-") for row in data["openingHours"]]
        oh = OpeningHours()
        oh.from_linked_data({"openingHours": hours_fixed}, "%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()
        apply_category(Categories.BANK, item)
        yield item
