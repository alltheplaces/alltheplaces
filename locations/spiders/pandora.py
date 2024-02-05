import re

import scrapy

from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class PandoraSpider(scrapy.spiders.SitemapSpider):
    name = "pandora"
    item_attributes = {
        "brand": "Pandora",
        "brand_wikidata": "Q2241604",
    }
    download_delay = 0.2
    allowed_domains = ["pandora.net"]
    sitemap_urls = ["https://stores.pandora.net/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/stores\.pandora\.net\/[^(?{2,})]+-([\w\d]+)\.html$", "parse_store")]

    def parse_store(self, response):
        yield self.parse_item(response, self.sitemap_rules[0][0])

    @staticmethod
    def parse_item(response, ref_regex) -> Feature:
        ld_item = LinkedDataParser.find_linked_data(response, "JewelryStore")

        if not ld_item:
            return

        if not ld_item.get("telephone"):
            ld_item["telephone"] = ld_item["address"].get("telephone")

        if ld_item.get("openingHours") and isinstance(ld_item["openingHours"], str):
            ld_item["openingHours"] = re.findall(r"\w{2} \d{2}:\d{2} - \d{2}:\d{2}", ld_item["openingHours"])

        if not ld_item.get("branchCode") and not ld_item.get("@id"):
            ld_item["branchCode"] = re.match(ref_regex, response.url).group(1)

        item = LinkedDataParser.parse_ld(ld_item)
        if item:
            if item["state"] == "JE":
                item["state"] = "JE-JerseyIsSpecial"
            # In many countries "state" is set to "country-region", unpick and discard region
            splits = item["state"].split("-")
            if len(splits) == 2 and len(splits[0]) == 2:
                item["state"] = None
                item["country"] = splits[0]
            return item
