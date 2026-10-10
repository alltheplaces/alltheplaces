from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class RoomAndBoardUSSpider(SitemapSpider, StructuredDataSpider):
    name = "room_and_board_us"
    item_attributes = {"brand_wikidata": "Q7366240"}
    sitemap_urls = ["https://www.roomandboard.com/static.xml"]
    sitemap_rules = [(r"/stores/[^/]+$", "parse")]
    # Excludes "delivery-center-schema-data" LocalBusiness blocks present on the
    # same pages, which are distribution facilities, not public showrooms.
    wanted_types = ["FurnitureStore"]
    # Some stores have no direct line; without this, the fallback phone
    # extractor picks up the shared national customer care number instead.
    search_for_phone = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
