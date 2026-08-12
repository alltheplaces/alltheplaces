import html

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CuisinellaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cuisinella_fr"
    item_attributes = {"brand": "Cuisinella", "brand_wikidata": "Q3007012"}
    sitemap_urls = ["https://www.ma.cuisinella/robots.txt"]
    sitemap_rules = [(r"/fr-fr/magasins/[\w-]+/[\w-]+", "parse")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        latitude = (ld_data.get("geo") or {}).get("latitude")
        if isinstance(latitude, str) and latitude.endswith("?.Latitude"):
            lat_lon = latitude.split("?", 1)
            if lat_lon[0]:
                ld_data["geo"]["latitude"], ld_data["geo"]["longitude"] = lat_lon[0].split(", ", 1)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["facebook"] = None
        if item.get("name"):
            item["branch"] = html.unescape(item.pop("name"))
            apply_category(Categories.SHOP_KITCHEN, item)
            yield item
