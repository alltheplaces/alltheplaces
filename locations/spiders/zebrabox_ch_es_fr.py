from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ZebraboxCHESFRSpider(SitemapSpider, StructuredDataSpider):
    name = "zebrabox_ch_es_fr"
    item_attributes = {"brand": "Zebrabox"}
    sitemap_urls = [
        "https://www.zebrabox.ch/sitemap.xml",
        "https://www.zebrabox.es/sitemap.xml",
        "https://www.zebrabox.fr/sitemap.xml",
    ]
    sitemap_rules = [(r"/en/locations/(?!region-|western-|eastern-)[^/]+$", "parse_sd")]
    drop_attributes = {"image", "facebook", "opening_hours"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Zebrabox ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
