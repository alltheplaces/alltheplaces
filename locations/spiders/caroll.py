import json
import re
from datetime import datetime
from typing import AsyncIterator, Iterable

from scrapy import Request, Selector
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

# Store pages also exist on the Belgian and Swiss sites, in each local language.
LOCALISED_PATHS = {
    "BE": {"fr": "/fr_be/magasins-", "nl": "/nl_be/boetiek-"},
    "CH": {"fr": "/fr_ch/magasins-", "de": "/de_ch/magasins-"},
}


class CarollSpider(JSONBlobSpider):
    name = "caroll"
    item_attributes = {"brand": "Caroll", "brand_wikidata": "Q63063871", "name": "Caroll"}
    # robots.txt disallows /on/demandware.store/.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        # Cloudflare bans Zyte's httpResponseBody here; only browserHtml gets through.
        yield Request(
            "https://www.caroll.com/on/demandware.store/Sites-CRL_FR_SFRA-Site/fr_FR/Stores-FindStores?lat=46.6&long=2.4&radius=20000&showMap=false",
            meta={"zyte_api": {"browserHtml": True, "geolocation": "FR"}},
        )

    def extract_json(self, response: TextResponse) -> list[dict]:
        # The browser renders the JSON body inside a <pre>.
        data = json.loads(response.xpath("//pre/text()").get(""))
        cards = Selector(text=data["storesResultsHtml"]).css(".card-body[id]")
        self.websites = {card.attrib["id"]: card.css(".storelocator-link::attr(href)").get() for card in cards}
        return data["stores"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        custom = feature.get("custom") or {}
        # Department store corners and multi-brand Sarenza Studio shops are out of scope.
        if custom.get("BMNR_Type") == "Grands Magasins and MarketPlace" or custom.get("BMNR_Multi"):
            return

        if branch := item.pop("name", None):
            item["branch"] = re.sub(r"^caroll\s+", "", branch, flags=re.IGNORECASE)
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        # The source tags the Monaco store as FR.
        if item.get("country") == "FR" and (item.get("postcode") or "").startswith("980"):
            item["country"] = "MC"
        # Store pages without a slug (Portugal, Luxembourg, Monaco...) are empty shells.
        website = self.websites.get(item["ref"]) or ""
        if re.search(r"/magasins-.+-\d+\.html$", website):
            if paths := LOCALISED_PATHS.get(item.get("country")):
                for language, path in paths.items():
                    item["extras"][f"website:{language}"] = website.replace("/fr_fr/magasins-", path)
                website = item["extras"]["website:fr"]
            item["website"] = website
        if closing_date := custom.get("BMNR_dateFermetureDefinitive"):
            try:
                set_closed(item, datetime.strptime(closing_date, "%d%m%Y"))
            except ValueError:
                self.logger.warning(f"Store {item['ref']}: unparsable closing date {closing_date!r}")

        try:
            oh = OpeningHours()
            for day, hours in json.loads(custom.get("BMNR_horaires") or "{}").items():
                if not (day := sanitise_day(day, DAYS_FR)):
                    continue
                # Days without a lunch break only fill ouverture_matin and fermeture_apresmidi.
                if hours.get("fermeture_matin") or hours.get("ouverture_apresmidi"):
                    oh.add_range(day, hours.get("ouverture_matin"), hours.get("fermeture_matin"), "%H%M")
                    oh.add_range(day, hours.get("ouverture_apresmidi"), hours.get("fermeture_apresmidi"), "%H%M")
                else:
                    oh.add_range(day, hours.get("ouverture_matin"), hours.get("fermeture_apresmidi"), "%H%M")
            item["opening_hours"] = oh
        except (ValueError, AttributeError):
            self.logger.warning(f"Store {item['ref']}: unparsable hours {custom.get('BMNR_horaires')!r}")

        # NSI's Caroll entry doesn't cover Belgium, Luxembourg or Monaco.
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
