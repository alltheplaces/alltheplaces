import json
import re
from typing import AsyncIterator, Iterable

from scrapy.http import Request, TextResponse

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider

# Coop's "Verkaufsstellen" (points of sale) search covers every banner in
# the Coop Group (supermarkets, Pronto convenience/fuel stations,
# restaurants, pharmacies, Interdiscount, Christ, etc). Sibling spiders
# already exist for some of these banners (coop_pronto_ch, coop_restaurant_ch,
# coop_vitality_ch); this spider is scoped to "retail" only, which is the
# flagship Coop Supermarkt banner.
DETAIL_URL = "https://www.coop.ch/de/unternehmen/standorte-und-oeffnungszeiten/detail.html/{}/{}.html"


class CoopCHSpider(StructuredDataSpider, CamoufoxSpider):
    name = "coop_ch"
    item_attributes = {"brand": "Coop", "brand_wikidata": "Q432564", "name": "Coop"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS
    # Every detail page carries the same corporate "Share on Twitter/Facebook"
    # links in its page chrome, not a branch-specific social profile; the
    # Twitter one isn't even a handle, just the "intent/tweet" share URL path.
    drop_attributes = {"twitter", "facebook"}

    async def start(self) -> AsyncIterator[Request]:
        # The whole site sits behind DataDome, so even the JSON API used by
        # the store locator widget must be requested via a real browser.
        # A single query centred on Switzerland with a generous "end" value
        # returns every "retail" (Coop Supermarkt) location in one response
        # (foundVstsSize == len(vstList), i.e. nothing is truncated).
        url = (
            "https://www.coop.ch/de/unternehmen/standorte-und-oeffnungszeiten.getvstlist.json"
            "?lat=46.8&lng=8.2&start=1&end=5000&filterFormat=retail&filterAttribute=&filterOpen=false&gasIndex=0"
        )
        yield Request(url, callback=self.parse_list)

    def parse_list(self, response: TextResponse) -> Iterable[Request]:
        # Camoufox renders the raw JSON response body inside a <pre> element.
        data = json.loads(re.search(r"<pre>(.*)</pre>", response.text, re.S).group(1))
        for store in data["vstList"]:
            detail_url = DETAIL_URL.format(store["betriebsNummerId"]["id"], store["prettyUrlName"])
            yield Request(detail_url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = re.search(r"/detail\.html/(\d+)/", response.url).group(1)
        item["branch"] = item.pop("name", None)
        item["country"] = "CH"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
