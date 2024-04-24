from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PremierurgentcareSpider(SitemapSpider, StructuredDataSpider):
    name = "premierurgentcare"
    item_attributes = {"brand": "Premier Urgent Care"}
    allowed_domains = ["www.premier.care"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    sitemap_urls = ["https://www.premier.care/sitemap.xml"]
    # Example:     # https://www.premier.care/locations/thumbs-up-temple/
    sitemap_rules = [(r"/locations/[\w-]+/$", "parse_sd")]
    wanted_types = ["MedicalOrganization"]
