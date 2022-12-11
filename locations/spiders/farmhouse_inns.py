from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class FarmhouseInnsSpider(SitemapSpider):
    name = "farmhouse_inns"
    item_attributes = {
        "brand": "Farmhouse Inns",
        "brand_wikidata": "Q105504972",
        "country": "GB",
    }
    sitemap_urls = ["https://www.farmhouseinns.co.uk/xml-sitemap"]
    sitemap_rules = [(r"https:\/\/www\.farmhouseinns\.co\.uk\/pubs\/([-\w]+)\/([-\w]+)\/$", "parse")]

    def parse(self, response):
        yield LinkedDataParser.parse(response, "BarOrPub")
