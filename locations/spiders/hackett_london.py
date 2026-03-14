from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HackettLondonSpider(SitemapSpider, StructuredDataSpider):
    name = "hackett_london"
    item_attributes = {"brand": "Hackett London", "brand_wikidata": "Q1136426"}
    sitemap_urls = ["https://storelocator.hackett.com/sitemap.xml"]
    sitemap_rules = [
        ("https://storelocator.hackett.com/hackett-", "parse"),
        # ("https://storelocator.hackett.com/hackett-london-regent-street-193-564e196a7412", "parse"),
    ]
    wanted_types = ["ClothingStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].startswith("Hackett Outlet "):
            item["branch"] = item.pop("name").removeprefix("Hackett Outlet ")
            item["name"] = "Hackett Outlet"
        else:
            item["branch"] = item.pop("name").removeprefix("Hackett ").removeprefix("London ")

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
