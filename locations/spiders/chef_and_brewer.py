from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class ChefAndBrewerSpider(SitemapSpider):
    name = "chef_and_brewer"
    item_attributes = {
        "brand": "Chef & Brewer",
        "brand_wikidata": "Q5089491",
        "country": "GB",
    }
    sitemap_urls = ["https://www.chefandbrewer.com/xml-sitemap"]
    sitemap_rules = [(r"https:\/\/www\.chefandbrewer\.com\/pubs\/([-\w]+)\/([-\w]+)\/$", "parse")]

    def parse(self, response):
        yield LinkedDataParser.parse(response, "BarOrPub")
