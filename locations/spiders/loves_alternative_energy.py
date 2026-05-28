import json

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class LovesAlternativeEnergySpider(SitemapSpider):
    name = "loves_alternative_energy"
    item_attributes = {"brand": "Love's Alternative Energy", "brand_wikidata": "Q139895750"}
    sitemap_urls = ["https://www.lovesalternativeenergy.com/sitemap-locations.xml"]
    sitemap_rules = [("/loves-alternative-energy-public-cng-", "parse")]

    def parse(self, response: TextResponse, **kwargs):
        details = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        location = DictParser.get_nested_key(details, "locationData")
        item = DictParser.parse(location)
        item["street_address"] = item.pop("addr_full")
        item["name"] = location["siteName"]
        item["website"] = response.url

        apply_category(Categories.FUEL_STATION, item)

        yield item
