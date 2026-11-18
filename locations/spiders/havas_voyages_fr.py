from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HavasVoyagesFRSpider(SitemapSpider, StructuredDataSpider):
    name = "havas_voyages_fr"
    item_attributes = {"brand": "Havas Voyages", "brand_wikidata": "Q57628091", "name": "Havas Voyages"}
    allowed_domains = ["agences.havas-voyages.fr"]
    sitemap_urls = ["https://agences.havas-voyages.fr/locationsitemap1.xml"]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Havas Voyages ")
        item["ref"] = response.url.split("/")[-1].split("-", 1)[0]
        # Most agencies share the same stock interior photo
        if "agence-interieur" in (item.get("image") or ""):
            item["image"] = None
        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        yield item
