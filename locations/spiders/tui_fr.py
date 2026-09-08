from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TuiFRSpider(SitemapSpider, StructuredDataSpider):
    name = "tui_fr"
    item_attributes = {"brand": "TUI", "brand_wikidata": "Q573103"}
    sitemap_urls = ["https://agences-de-voyages.tui.fr/sitemap.xml"]
    sitemap_rules = [(r"https://agences-de-voyages.tui.fr/.*\d$", "parse_sd")]
    wanted_types = ["TravelAgency"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/TUIFrance/":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("Agence de voyage TUI Store ").removeprefix("TUI STORE ").removeprefix("TUI STORE ").removeprefix("Agence adhérente TUI ").removeprefix("TUI Store ").removeprefix("Agence de voyage TUI STORE ")
        
        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        yield item
