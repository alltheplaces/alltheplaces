from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BlindsToGoSpider(CrawlSpider, StructuredDataSpider):
    name = "blinds_to_go"
    item_attributes = {"brand": "Blinds to Go", "brand_wikidata": "Q123409913"}
    start_urls = ["https://www.blindstogo.com/en/stores"]
    rules = [Rule(LinkExtractor("/en/stores/"), callback="parse")]
    wanted_types = ["HomeGoodsStore"]
    skip_auto_cc_spider_name = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        if image := item.get("image"):
            item["image"] = image.strip()

        item["extras"]["website:en"] = response.url
        item["extras"]["website:fr"] = response.xpath('//link[@rel="alternate"][@hreflang="fr-CA"]/@href').get()

        item["website"] = (
            item["extras"]["website:en"] if item["name"] == "Blinds To Go" else item["extras"]["website:fr"]
        )

        apply_category(Categories.SHOP_WINDOW_BLIND, item)

        yield item
