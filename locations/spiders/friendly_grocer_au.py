from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class FriendlyGrocerAUSpider(SitemapSpider):
    name = "friendly_grocer_au"
    item_attributes = {"brand": "Friendly Grocer", "brand_wikidata": "Q24190419"}
    allowed_domains = ["friendlygrocer.com.au"]
    sitemap_urls = ["https://friendlygrocer.com.au/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/friendlygrocer\.com\.au\/", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        js_blob = response.xpath('//script[contains(text(), "const properties = [")]').get()
        if not js_blob or "lat: ," in js_blob:
            # Page is not a store page. It is not possible to easily determine
            # which pages in the sitemap are store pages or other misc pages
            # so we have to try each one to find out if it's a store page.
            return
        js_blob = js_blob.split("const properties = [", 1)[1].split("]", 1)[0]
        store_data = parse_js_object(js_blob)
        properties = {
            "ref": response.url,
            "branch": store_data["description"].removeprefix("Friendly Grocer "),
            "addr_full": store_data["address"],
            "lat": store_data["position"]["lat"],
            "lon": store_data["position"]["lng"],
            "website": response.url,
        }
        apply_category(Categories.SHOP_CONVENIENCE, properties)
        yield Feature(**properties)
