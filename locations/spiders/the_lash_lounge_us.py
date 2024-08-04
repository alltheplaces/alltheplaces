from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TheLashLoungeUSSpider(SitemapSpider, StructuredDataSpider):
    name = "the_lash_lounge_us"
    item_attributes = {"brand": "The Lash Lounge", "brand_wikidata": "Q112765439"}
    sitemap_urls = ["https://www.thelashlounge.com/subsites-sitemap.xml"]
    sitemap_follow = ["storelocator"]
    sitemap_rules = [(r"https:\/\/www\.thelashlounge\.com\/\w+-\w+-\w+/$", "parse_sd")]
    wanted_types = ["BeautySalon"]
