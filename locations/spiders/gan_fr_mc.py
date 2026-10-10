from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GanFrMcSpider(SitemapSpider, StructuredDataSpider):
    name = "gan_fr_mc"
    item_attributes = {"brand": "Gan", "brand_wikidata": "Q3095058"}
    sitemap_urls = [
        "https://www.agence.gan.fr/locationsitemap1.xml",
        "https://www.agence.gan.fr/locationsitemap2.xml",
    ]
    wanted_types = ["InsuranceAgency"]
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
