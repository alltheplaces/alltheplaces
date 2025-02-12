from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MassageEnvySpider(SitemapSpider, StructuredDataSpider):
    name = "massage_envy"
    item_attributes = {"brand": "Massage Envy", "brand_wikidata": "Q10327170"}
    allowed_domains = ["locations.massageenvy.com"]
    sitemap_urls = ("https://locations.massageenvy.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://locations.massageenvy.com/[^/]+/[^/]+/[^/]+.html$", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}
