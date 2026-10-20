import re
from typing import AsyncIterator, Iterable

from scrapy.http import Request, Response, TextResponse

from locations.categories import Extras
from locations.items import Feature
from locations.storefinders.lib_cal import LibCalSpider

CARD_REGEX = re.compile(r"^(?P<address>.+?),?\s*Phone:\s*,?\s*(?P<phone>[^,]+?)\s*(?:,\s*Fax:\s*(?P<fax>.+))?$")
POSTCODE_REGEX = re.compile(r"\b(MN)\s+(\d{5})$")


class EastCentralRegionalLibraryUSSpider(LibCalSpider):
    name = "east_central_regional_library_us"
    item_attributes = {"operator": "East Central Regional Library", "operator_wikidata": "Q69480691"}
    libcal_host = "ecrlib.libcal.com"
    libcal_iid = 5144
    country = "US"

    async def start(self) -> AsyncIterator[Request]:
        # LibCal has hours and a branch URL but no address, phone or
        # coordinates, so the cards on the library's own locations page are
        # read first. They also carry a working branch link, where LibCal's
        # URL for Mille Lacs Lake is a dead page.
        yield Request("https://ecrlib.org/locations-hours/", callback=self.parse_locations_page)

    async def parse_locations_page(self, response: Response) -> AsyncIterator[Request]:
        self.cards = {}
        for card in response.css(".elementor-inner-column"):
            if label := card.css(".elementor-widget-heading").xpath("normalize-space(string(.))").get():
                self.cards[label] = card
        async for request in super().start():
            yield request

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs
    ) -> Iterable[Feature | Request]:
        # Cards are labelled with the town alone, e.g. "Aitkin" for the
        # "Aitkin Public Library" of LibCal. The page also has cards for the
        # headquarters and the outreach van, which LibCal does not list.
        label = max((label for label in self.cards if (item["name"] or "").startswith(label)), key=len, default=None)
        if label is None:
            self.logger.warning("No card on the locations page for %s", item["name"])
            yield item
            return
        card = self.cards[label]
        item["website"] = card.css(".elementor-widget-button a::attr(href)").get() or item["website"]

        lines = card.css(".elementor-widget-text-editor p")[0].xpath(".//text()").getall()
        text = ", ".join(filter(None, (re.sub(r"\s+", " ", line.replace("\xa0", " ")).strip() for line in lines)))
        if match := CARD_REGEX.match(text):
            # Street and city run together without a separator on most cards
            # (e.g. "300 Fifth St. SE Pine City, MN 55063"), so the address is
            # not reliably splittable.
            item["addr_full"] = match["address"]
            item["phone"] = match["phone"]
            if fax := match["fax"]:
                item["extras"][Extras.FAX.value] = fax
            if postcode_match := POSTCODE_REGEX.search(match["address"]):
                item["state"], item["postcode"] = postcode_match.groups()
        yield item
