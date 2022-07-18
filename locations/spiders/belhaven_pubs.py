from scrapy.spiders import SitemapSpider

from locations.items import GeojsonPointItem
from locations.utils import find_linked_data


class BelhavenPubsSpider(SitemapSpider):
    name = "belhaven_pubs"
    item_attributes = {
        "brand": "Belhaven Pubs",
        "brand_wikidata": "Q105516156",
        "country": "GB",
    }
    sitemap_urls = ["https://www.belhavenpubs.co.uk/xml-sitemap"]
    sitemap_rules = [
        (r"https:\/\/www\.belhavenpubs\.co\.uk\/pubs\/([-\w]+)\/([-\w]+)\/$", "parse")
    ]

    def parse(self, response):
        pub = find_linked_data(response, "BarOrPub")

        if pub:
            item = GeojsonPointItem()
            item.from_linked_data(pub)

            item["website"] = response.url

            yield item
