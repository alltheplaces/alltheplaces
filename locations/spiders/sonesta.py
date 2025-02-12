from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SonestaSpider(SitemapSpider, StructuredDataSpider):
    name = "sonesta"
    item_attributes = {"brand": "Sonesta", "brand_wikidata": "Q81003878"}
    sitemap_urls = ["https://www.sonesta.com/sitemap/sitemap-index.xml"]
    # https://www.sonesta.com/sonesta-simply-suites/al/birmingham/sonesta-simply-suites-birmingham-hoover
    sitemap_rules = [(r"^https\:\/\/www\.sonesta\.com/[\w-]+/\w\w/[\w-]+/[\w-]+$", "parse_sd")]
    wanted_types = ["Hotel"]
    drop_attributes = {"email"}

    def post_process_item(self, item, response, ld_data):
        # Pages without lat lon are test pages
        lat = ld_data.get("latitude")
        lon = ld_data.get("longitude")
        if lat and lon:
            item["lat"] = lat
            item["lon"] = lon
            yield item
