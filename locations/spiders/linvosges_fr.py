from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LinvosgesFRSpider(CrawlSpider, StructuredDataSpider):
    name = "linvosges_fr"
    item_attributes = {"brand": "Linvosges", "brand_wikidata": "Q94359140"}
    start_urls = ["https://www.linvosges.com/fr/nos-magasins/"]
    rules = [
        Rule(LinkExtractor(allow=r"fr/nos-magasins/[\w-]+"), callback="parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # NSI has exactly one Linvosges entry (only covering "fx", the legacy
        # code for Metropolitan France that the location matcher does not
        # alias to "fr"), so apply the category directly rather than relying
        # on NSI location matching.
        apply_category(Categories.SHOP_HOUSEHOLD_LINEN, item)
        yield item
