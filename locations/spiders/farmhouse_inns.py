from scrapy.spiders import SitemapSpider

from locations.items import GeojsonPointItem
from locations.utils import find_linked_data


class FarmhouseInnsSpider(SitemapSpider):
    name = "farmhouse_inns"
    item_attributes = {
        "brand": "Farmhouse Inns",
        "brand_wikidata": "Q105504972",
        "country": "GB",
    }
    sitemap_urls = ["https://www.farmhouseinns.co.uk/xml-sitemap"]
    sitemap_rules = [
        (r"https:\/\/www\.farmhouseinns\.co\.uk\/pubs\/([-\w]+)\/([-\w]+)\/$", "parse")
    ]

    def parse(self, response):
        pub = find_linked_data(response, "BarOrPub")

        if pub:
            item = GeojsonPointItem()
            item.from_linked_data(pub)

            item["website"] = response.url

            yield item
