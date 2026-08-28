from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class MGENFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mgen_fr"
    item_attributes = {
        "brand": "MGEN",
        "brand_wikidata": "Q3331039",
        "extras": Categories.OFFICE_INSURANCE.value,
    }
    sitemap_urls = ["https://proximite.mgen.fr/locationsitemap1.xml"]
    sitemap_rules = [(r"https://proximite\.mgen\.fr/.+", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}
