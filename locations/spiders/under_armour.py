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

    def parse(self, response):
        for script in response.xpath('//script[@type="application/ld+json"]'):
            text = script.root.text
            # commented-out line
            text = re.sub(r" +//.*", "", text, flags=re.M)
            script.root.text = text
        item = LinkedDataParser.parse(response, "SportingGoodsStore")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
