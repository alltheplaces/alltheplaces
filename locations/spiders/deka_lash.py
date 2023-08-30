from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DekaLashSpider(SitemapSpider, StructuredDataSpider):
    name = "deka_lash"
    item_attributes = {"brand": "Deka Lash", "brand_wikidata": "Q120505973"}
    sitemap_urls = ["https://dekalash.com/page-sitemap.xml"]
    sitemap_rules = [(r"/find-a-studio/.+/.+/$", "parse")]
    wanted_types = ["BeautySalon"]
