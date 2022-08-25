from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class TheCooperativeGroupSpider(SitemapSpider):
    name = "the_cooperative_group"
    item_attributes = {"brand": "The Co-operative Group", "brand_wikidata": "Q117202"}
    sitemap_urls = [
        "https://www.coop.co.uk/store-finder/sitemap.xml",
        "https://www.coop.co.uk/funeralcare/funeral-directors/sitemap.xml",
    ]
    sitemap_rules = [
        (
            r"https:\/\/www\.coop\.co\.uk\/store-finder\/[-\w]+\/[-\w]+$",
            "parse_store",
        ),
        (
            r"https:\/\/www\.coop\.co\.uk\/funeralcare\/funeral-directors\/",
            "parse_funeralcare",
        ),
    ]

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "ConvenienceStore")

        if item is None:
            return

        item["ref"] = item["website"]

        return item

    def parse_funeralcare(self, response):
        item = LinkedDataParser.parse(response, "LocalBusiness")

        if item is None:
            return

        item["ref"] = item["website"]

        return item
