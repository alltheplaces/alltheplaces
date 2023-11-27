import html
import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NeonetPLSpider(SitemapSpider):
    name = "neonet_pl"
    item_attributes = {"brand": "Neonet", "brand_wikidata": "Q11790622"}
    sitemap_urls = ["https://sklepy.neonet.pl/sitemap.xml"]
    sitemap_rules = [(r"/polska/.*[0-9]$", "parse")]

    def parse(self, response):
        data = json.loads(
            html.unescape(response.xpath('//*[@type = "application/ld+json"]').xpath("normalize-space()").get())
        )[1]
        item = DictParser.parse(data)
        item["ref"] = data.get("@id")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].from_linked_data(data)
        yield item
