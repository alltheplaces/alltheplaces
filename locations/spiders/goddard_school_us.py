from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoddardSchoolUSSpider(SitemapSpider, StructuredDataSpider):
    name = "goddard_school_us"
    item_attributes = {"brand": "Goddard School", "brand_wikidata": "Q5576260"}
    sitemap_urls = ["https://www.goddardschool.com/sitemap.xml"]
    sitemap_rules = [(r"/schools/[a-z]{2}/[-\w]+/[-\w]+$", "parse_sd")]
