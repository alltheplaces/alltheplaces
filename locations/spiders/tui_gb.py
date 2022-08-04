from scrapy.spiders import SitemapSpider

from locations.google_url import url_to_coords
from locations.linked_data_parser import LinkedDataParser


class TUISpider(SitemapSpider):
    name = "tui_gb"
    item_attributes = {
        "brand": "Q7795876",
        "brand_wikidata": "Q7795876",
        "country": "GB",
    }
    sitemap_urls = ["https://www.tui.co.uk/sitemap/sitemap.xml"]
    sitemap_rules = [
        (
            r"^https:\/\/www\.tui\.co\.uk\/shop-finder\/([-\w]+)$",
            "parse",
        ),
    ]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0"
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"].startswith("https://www.tui.co.uk/shop-finder/directory"):
                pass
            else:
                yield entry

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Store")

        item["ref"] = response.url.split("/")[-1]

        if item.get("lat") is None or item.get("lon") is None:
            item["lat"], item["lon"] = url_to_coords(
                response.xpath('//p[@class="-Directions"]/a/@href').get()
            )

        if "INSIDE NEXT" in item["name"].upper():
            item["located_in"] = "Next"
            item["located_in_wikidata"] = "Q246655"

        return item
