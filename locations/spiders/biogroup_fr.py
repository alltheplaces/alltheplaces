from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BiogroupFRSpider(SitemapSpider, StructuredDataSpider):
    name = "biogroup_fr"
    item_attributes = {"brand": "Biogroup", "brand_wikidata": "Q101559741"}
    sitemap_urls = ["https://laboratoires.biogroup.fr/robots.txt"]
    sitemap_rules = [(r"fr/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["MedicalClinic"]
