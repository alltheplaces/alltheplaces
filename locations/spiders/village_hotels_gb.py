import html

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class VillageHotelsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "village_hotels_gb"
    item_attributes = {"brand": "Village Hotels", "brand_wikidata": "Q16963550"}
    sitemap_urls = ["https://www.village-hotels.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https://www.village-hotels.co.uk/([^/]+)$", "parse")]
    wanted_types = ["Hotel"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = html.unescape(item.pop("name")).replace("Village Hotel - ", "")
        if ld_data.get("hasMap"):
            item["lat"], item["lon"] = (
                ld_data["hasMap"].replace("https://www.google.com/maps/search/?api=1&query=", "").split(", ")
            )
        else:
            return
        item["addr_full"] = item.pop("street_address")
        item.pop("twitter", None)
        apply_category(Categories.HOTEL, item)
        yield item
