import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SportsmansWarehouseUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sportsmans_warehouse_us"
    item_attributes = {"brand": "Sportsman's Warehouse", "brand_wikidata": "Q7579979"}
    allowed_domains = ["stores.sportsmans.com"]
    sitemap_urls = ["https://stores.sportsmans.com/sitemap.xml"]
    sitemap_rules = [(r"^https://stores\.sportsmans\.com/sportsmans-warehouse/us/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    drop_attributes = {"facebook", "twitter"}  # brand's own generic social accounts, not store-specific

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = response.url

        # No coordinates are present in the JSON-LD, but the page's embedded
        # Yext hydration data carries the location's own published pin.
        if coords := re.search(
            r'"yextDisplayCoordinate":\{"latitude":([\d.-]+),"longitude":([\d.-]+)\}', response.text
        ):
            item["lat"], item["lon"] = coords.groups()

        apply_category(Categories.SHOP_OUTDOOR, item)
        yield item
