from scrapy.spiders import SitemapSpider

from locations.items import GeojsonPointItem
from locations.utils import find_linked_data


class ChefAndBrewerSpider(SitemapSpider):
    name = "chef_and_brewer"
    item_attributes = {
        "brand": "Chef & Brewer",
        "brand_wikidata": "Q5089491",
        "country": "GB",
    }
    sitemap_urls = ["https://www.chefandbrewer.com/xml-sitemap"]
    sitemap_rules = [
        (r"https:\/\/www\.chefandbrewer\.com\/pubs\/([-\w]+)\/([-\w]+)\/$", "parse")
    ]

    def parse(self, response):
        pub = find_linked_data(response, "BarOrPub")

        if pub:
            item = GeojsonPointItem()
            item.from_linked_data(pub)

            item["website"] = response.url

            yield item
