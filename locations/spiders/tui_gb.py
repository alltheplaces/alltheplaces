from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.linked_data_parser import LinkedDataParser
from locations.user_agents import BROWSER_DEFAULT


class TuiGBSpider(SitemapSpider):
    name = "tui_gb"
    item_attributes = {
        "brand": "TUI",
        "brand_wikidata": "Q7795876",
        "country": "GB",
    }
    sitemap_urls = ["https://www.tui.co.uk/sitemap/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.tui\.co\.uk\/shop-finder\/([-\w]+)$", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"].startswith("https://www.tui.co.uk/shop-finder/directory"):
                pass
            else:
                yield entry

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = LinkedDataParser.parse(response, "Store")

        item["ref"] = response.url.split("/")[-1]

        if item.get("lat") is None or item.get("lon") is None:
            item["lat"], item["lon"] = url_to_coords(response.xpath('//p[@class="-Directions"]/a/@href').get())

        if "INSIDE NEXT" in item["name"].upper():
            item["located_in"] = "Next"
            item["located_in_wikidata"] = "Q246655"
        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        return item
