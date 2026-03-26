from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tesco_gb import TescoGBSpider, set_located_in
from locations.structured_data_spider import StructuredDataSpider


class YoSushiSpider(SitemapSpider, StructuredDataSpider):
    name = "yo_sushi"
    item_attributes = {"brand": "YO! Sushi", "brand_wikidata": "Q3105441"}
    sitemap_urls = ["https://yosushi.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://yosushi\.com/restaurants/[-\w]+", "parse"),
        ("https://yosushi.com/aberdeen", "parse"),
        ("https://yosushi.com/birmingham-selfridges", "parse"),
        ("https://yosushi.com/luton-airport", "parse"),
        ("https://yosushi.com/york-outlet", "parse"),
    ]
    wanted_types = ["Restaurant"]
    drop_attributes = {"facebook", "twitter", "email"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = ld_data["latitude"], ld_data["longitude"]
        item["branch"] = item.pop("name")
        if (ld_data.get("description") and "kiosk" in ld_data["description"].lower()) or "-kiosk" in response.url:
            apply_category(Categories.FAST_FOOD, item)
        else:
            apply_category(Categories.RESTAURANT, item)

        if "-extra" in response.url or "tesco extra" in item["branch"].lower():
            set_located_in(TescoGBSpider.TESCO_EXTRA, item)
        elif "-superstore" in response.url:
            set_located_in(TescoGBSpider.TESCO, item)
        elif "-express" in response.url:
            set_located_in(TescoGBSpider.TESCO_EXPRESS, item)
        if item["phone"] == "03456779207":
            item.pop("phone", None)

        yield item
