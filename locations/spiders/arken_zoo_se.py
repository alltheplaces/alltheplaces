import re
from urllib.parse import urljoin

from chompjs import parse_js_object
from scrapy import Selector
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider

# The generic national customer-service line/email, present on almost every
# store page's structured data instead of a branch-specific contact.
NATIONAL_HOTLINE_DIGITS = "104906255"
NATIONAL_EMAIL = "kundtjanst@arkenzoo.se"


class ArkenZooSESpider(StructuredDataSpider):
    name = "arken_zoo_se"
    item_attributes = {"brand": "Arken Zoo", "brand_wikidata": "Q16497087"}
    start_urls = ["https://www.arkenzoo.se/info/vara-butiker"]
    wanted_types = ["LocalBusiness"]

    def parse(self, response: TextResponse, **kwargs):
        # The store locator page embeds a JS array of stores (link, lat, lon, street)
        # used to plot a Mapbox map. This is the only place coordinates are published.
        blob = re.search(r"var locations\s*=\s*(\[.*?\]);", response.text, re.S)
        if not blob:
            return
        for store in parse_js_object(blob.group(1)):
            if not store:
                continue
            link_html, lat, lon = store[0], store[1], store[2]
            if href := Selector(text=link_html).xpath("//a/@href").get():
                # hrefs are relative to the site root, not this /info/ page
                url = urljoin("https://www.arkenzoo.se/", href)
                yield response.follow(url, callback=self.parse_sd, meta={"lat": lat, "lon": lon})

    def iter_linked_data(self, response: Response):
        # Store pages nest the LocalBusiness under a WebPage's mainEntity, which the
        # default linked data lookup does not descend into.
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if ld_obj.get("@type") == "WebPage" and isinstance(ld_obj.get("mainEntity"), dict):
                yield ld_obj["mainEntity"]

    def post_process_item(self, item, response: Response, ld_item: dict, **kwargs):
        item["lat"] = response.meta.get("lat")
        item["lon"] = response.meta.get("lon")
        item["branch"] = item.pop("name").removeprefix("Arken Zoo").strip()
        if re.sub(r"\D", "", item.get("phone") or "").endswith(NATIONAL_HOTLINE_DIGITS):
            item["phone"] = None
        if item.get("email") == NATIONAL_EMAIL:
            item["email"] = None
        item["image"] = None  # same generic brand logo used on every store page
        apply_category(Categories.SHOP_PET, item)
        yield item
