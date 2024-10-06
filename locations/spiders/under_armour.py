import re

import scrapy

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class UnderArmourSpider(scrapy.spiders.SitemapSpider):
    name = "under_armour"
    item_attributes = {"brand": "Under Armour", "brand_wikidata": "Q2031485"}
    allowed_domains = ["underarmour.com"]
    sitemap_urls = [
        "https://store-locations.underarmour.com/robots.txt",
    ]
    sitemap_rules = [
        (r"https://store-locations\.underarmour\.com/.*/.*/.*/", "parse"),
    ]
    drop_attributes = {"image"}
    time_format = "%I:%M %p"

    def parse(self, response):
        for script in response.xpath('//script[@type="application/ld+json"]'):
            text = script.root.text
            # commented-out line
            text = re.sub(r" +//.*", "", text, flags=re.M)
            script.root.text = text

        ld_item = LinkedDataParser.find_linked_data(response, "SportingGoodsStore")
        item = LinkedDataParser.parse_ld(ld_item, time_format=self.time_format)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
