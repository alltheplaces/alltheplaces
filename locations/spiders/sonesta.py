from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SonestaSpider(SitemapSpider, StructuredDataSpider):
    download_delay = 0.2
    name = "sonesta"
    item_attributes = {"brand": "Sonesta", "brand_wikidata": "Q81003878"}
    sitemap_urls = ["https://www.sonesta.com/sitemap/sitemap-index.xml"]
    # https://www.sonesta.com/sonesta-simply-suites/al/birmingham/sonesta-simply-suites-birmingham-hoover
    sitemap_rules = [(r"^https\:\/\/www\.sonesta\.com/[\w-]+/\w\w/[\w-]+/[\w-]+$", "parse_sd")]
    wanted_types = ["Hotel"]

    def post_process_item(self, item, response, ld_data):
        # TODO: Establish why this is not just mapped for the Hotel type
        item["lat"] = ld_data["latitude"]
        item["lon"] = ld_data["longitude"]

        # TODO: The responses include a PostalAddress as well, ie: https://validator.schema.org/#url=https%3A%2F%2Fwww.sonesta.com%2Fsonesta-simply-suites%2Fal%2Fbirmingham%2Fsonesta-simply-suites-birmingham-hoover
        # However this is not readily parsed.

        yield item
