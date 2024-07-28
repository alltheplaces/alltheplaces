from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider

# Five Guys Microdata


class FiveGuysCASpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_ca"
    item_attributes = {"brand": "Five Guys", "brand_wikidata": "Q1131810"}
    sitemap_urls = ["https://restaurants.fiveguys.ca/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ca\/[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Five Guys ")

        yield item
