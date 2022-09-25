from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class IkesSpider(SitemapSpider):
    name = "ikes"
    item_attributes = {
        "brand": "Ike's Love & Sandwiches",
        "brand_wikidata": "Q112028897",
    }

    allowed_domains = ["locations.ikessandwich.com"]
    sitemap_urls = ["https://locations.ikessandwich.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/locations.ikessandwich.com\/.+\/",
            "parse",
        ),
    ]

    def parse(self, response):
        store_links = response.css(".sb-directory-list li a")
        yield from response.follow_all(store_links, callback=self.parse_store)

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "LocalBusiness")
        if item is None:
            return
        item["ref"] = response.url.split("/")[-2]
        yield item
