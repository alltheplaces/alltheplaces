from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BiogroupFRSpider(SitemapSpider, StructuredDataSpider):
    name = "biogroup_fr"
    item_attributes = {"brand": "Biogroup", "brand_wikidata": "Q101559741"}
    sitemap_urls = ["https://laboratoires.biogroup.fr/robots.txt"]
    sitemap_rules = [(r"fr/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["MedicalClinic"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # NSI has exactly one Biogroup entry (only covering "fx", the legacy
        # code for Metropolitan France that the location matcher does not
        # alias to "fr"), so apply the category directly rather than relying
        # on NSI location matching.
        apply_category(Categories.MEDICAL_LABORATORY, item)
        yield item
