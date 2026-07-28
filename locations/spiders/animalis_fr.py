from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AnimalisFRSpider(SitemapSpider, StructuredDataSpider):
    name = "animalis_fr"
    item_attributes = {"brand": "Animalis", "brand_wikidata": "Q2850015"}
    sitemap_urls = ["https://magasin.animalis.com/locationsitemap1.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # NSI has exactly one Animalis entry (only covering "fx", the legacy
        # code for Metropolitan France that the location matcher does not
        # alias to "fr"), so apply the category directly rather than relying
        # on NSI location matching.
        apply_category(Categories.SHOP_PET, item)
        yield item
