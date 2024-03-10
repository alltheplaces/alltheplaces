from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TargetOpticalSpider(SitemapSpider, StructuredDataSpider):
    name = "target_optical_us"
    # Presumably a sub brand of item_attributes = {"brand": "Luxottica", "brand_wikidata": "Q1878364"}
    item_attributes = {"brand": "Target Optical", "brand_wikidata": "Q19903688"}

    allowed_domains = ["local.targetoptical.com"]
    sitemap_urls = [
        "https://local.targetoptical.com/sitemap1.xml",
    ]
    # Example: ky/louisville/4101-towne-center-dr
    sitemap_rules = [(r"\w\w/[\w-]+/[\w-]+.html$", "parse_sd")]
