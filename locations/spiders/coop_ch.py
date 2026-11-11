import re
from typing import Any, AsyncIterator, Iterable

from scrapy import FormRequest
from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

# Coop's "Verkaufsstellen" (points of sale) search covers every banner in
# the Coop Group (supermarkets, Pronto convenience/fuel stations,
# restaurants, pharmacies, Interdiscount, Christ, etc). Sibling spiders
# already exist for some of these banners (coop_pronto_ch, coop_restaurant_ch,
# coop_vitality_ch); this spider is scoped to "retail" only, which is the
# flagship Coop Supermarkt banner.
DETAIL_URL = "https://www.coop.ch/de/unternehmen/standorte-und-oeffnungszeiten/detail.html/{}/{}.html"


class CoopCHSpider(StructuredDataSpider):
    name = "coop_ch"
    item_attributes = {"brand": "Coop", "brand_wikidata": "Q432564", "name": "Coop"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    # Every detail page carries the same corporate "Share on Twitter/Facebook"
    # links in its page chrome, not a branch-specific social profile; the
    # Twitter one isn't even a handle, just the "intent/tweet" share URL path.
    drop_attributes = {"twitter", "facebook"}

    async def start(self) -> AsyncIterator[FormRequest]:
        # Fetch cookies to avoid DataDome blockage
        yield FormRequest(
            url="https://api-js.datadome.co/js/",
            headers={
                "referer": "https://www.coop.ch/de/store-finder",
            },
            formdata={"ddk": "4E2D21855D176C1885A97CE16C8EC3"},
        )

    def parse(self, response: TextResponse, **kwargs) -> Any:
        # A single query centred on Switzerland with a generous "end" value
        # returns every "retail" (Coop Supermarkt) location in one response
        # (foundVstsSize == len(vstList), i.e. nothing is truncated).
        url = (
            "https://www.coop.ch/de/unternehmen/standorte-und-oeffnungszeiten.getvstlist.json"
            "?lat=46.8&lng=8.2&start=1&end=5000&filterFormat=retail&filterAttribute=&filterOpen=false&gasIndex=0"
        )
        yield JsonRequest(url=url, cookies={"cookie": response.json()["cookie"]}, callback=self.parse_list)

    def parse_list(self, response: TextResponse) -> Iterable[Request]:
        for store in response.json()["vstList"]:
            detail_url = DETAIL_URL.format(store["betriebsNummerId"]["id"], store["prettyUrlName"])
            yield Request(detail_url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = re.search(r"/detail\.html/(\d+)/", response.url).group(1)
        item["branch"] = item.pop("name", None)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
