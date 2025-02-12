from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BoostMobileUSSpider(SitemapSpider, StructuredDataSpider):
    name = "boost_mobile_us"
    item_attributes = {
        "brand": "Boost Mobile",
        "brand_wikidata": "Q4943790",
    }
    sitemap_urls = ["https://www.boostmobile.com/locations/sitemap-business-main-pages.xml"]
    sitemap_rules = [(r"/locations/bd/boost-mobile-[a-z]{2}-[-\w]", "parse_sd")]
