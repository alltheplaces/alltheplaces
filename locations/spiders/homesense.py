from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HomesenseSpider(SitemapSpider, StructuredDataSpider):
    name = "homesense"
    item_attributes = {"brand": "HomeSense", "brand_wikidata": "Q16844433"}
    sitemap_urls = ["https://locations.us.homesense.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/locations\.us\.homesense\.com\/\w{2}\/[-\w]+$", "parse_sd")]
    wanted_types = ["DepartmentStore"]
