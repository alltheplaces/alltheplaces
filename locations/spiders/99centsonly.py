from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class NinetyNineCentsOnlySpider(SitemapSpider):
    name = "99centsonly"
    item_attributes = {"brand": "99 Cents Only Stores", "brand_wikidata": "Q4646294"}
    allowed_domains = ["99only.com", "locations.99only.com"]
    download_delay = 2
    sitemap_urls = ["https://99only.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/99only\.com\/stores\/.*-\d*",
            "parse_store",
        ),
    ]
    requires_proxy = True

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Store")

        if item is None:
            return

        item["ref"] = response.url.strip(".html").rsplit("-")[-1]
        # The street address has whitespace at the end sometimes
        item["street_address"] = item["street_address"].strip()

        yield item
