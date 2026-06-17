import scrapy

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class NoicompriamoautoITSpider(scrapy.Spider):
    name = "noicompriamoauto_it"
    item_attributes = {
        "brand": "Noi Compriamo Auto",
        "brand_wikidata": "Q106502060",
    }
    start_urls = ["https://www.noicompriamoauto.it/filiali/"]

    def parse(self, response, **kwargs):
        for href in response.css("a[href^='/filiali/']::attr(href)").getall():
            if href == "/filiali/":
                continue
            yield response.follow(href, callback=self.parse_branch)

    def parse_branch(self, response):
        ld = LinkedDataParser.find_linked_data(response, "AutoDealer")
        if not ld:
            return

        # Times are in HH:MM:SS format on this site
        item = LinkedDataParser.parse_ld(ld, time_format="%H:%M:%S")

        # Ensure website is set to the branch page URL
        if not item.get("website"):
            item["website"] = response.url

        # Drop shared brand image (same URL across all branches)
        item.pop("image", None)

        # Extract branch name: "noicompriamoauto.it <City>" → "<City>"
        if item.get("name"):
            item["branch"] = item.pop("name").removeprefix("noicompriamoauto.it ").strip()

        # Use the URL slug as a stable ref
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]

        apply_category(Categories.SHOP_CAR, item)

        yield item
