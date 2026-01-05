from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

BRANDS = {
    "Americas Best Value Inn": "Q4742512",
    "Red Lion Hotels": "Q25047720",
    "Red Lion Inn & Suites": "Q25047720",
    "Sonesta ES Suites": "Q81007929",
    "Sonesta Select": "Q109272530",
    "Sonesta Simply Suites": "Q109272879",
}


class SonestaSpider(SitemapSpider, StructuredDataSpider):
    name = "sonesta"
    item_attributes = {"brand": "Sonesta", "brand_wikidata": "Q81003878"}
    sitemap_urls = ["https://www.sonesta.com/sitemap/sitemap-index.xml"]
    # https://www.sonesta.com/sonesta-simply-suites/al/birmingham/sonesta-simply-suites-birmingham-hoover
    sitemap_rules = [(r"^https\:\/\/www\.sonesta\.com/[\w-]+/\w\w/[\w-]+/[\w-]+$", "parse_sd")]
    wanted_types = ["Hotel"]
    search_for_email = False
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data):
        # Pages without lat lon are test pages
        lat = ld_data.get("latitude")
        lon = ld_data.get("longitude")
        if not lat or not lon:
            return

        item["lat"] = lat
        item["lon"] = lon

        item["brand"] = ld_data.get("brand", {}).get("name")
        item["brand_wikidata"] = BRANDS.get(item["brand"])

        apply_category(Categories.HOTEL, item)

        yield item
