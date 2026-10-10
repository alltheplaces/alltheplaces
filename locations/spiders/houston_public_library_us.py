import re
from typing import AsyncIterator, Iterable

from scrapy import Selector
from scrapy.http import Request, Response, TextResponse

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.storefinders.lib_cal import LibCalSpider

ADDRESS_REGEX = re.compile(r"^(.+?),?\s+(Houston),\s+(TX)\s+(\d{5})$")


class HoustonPublicLibraryUSSpider(LibCalSpider):
    name = "houston_public_library_us"
    item_attributes = {"operator": "Houston Public Library", "operator_wikidata": "Q1647690"}
    libcal_host = "calendar.houstonlibrary.org"
    libcal_iid = 3866
    country = "US"
    custom_settings = {"DOWNLOAD_DELAY": 10}

    async def start(self) -> AsyncIterator[Request]:
        # LibCal has no address for some branches and a wrong one for others,
        # so the cards on the library's own locations page are read first.
        yield Request("https://houstonlibrary.org/all-locations", callback=self.parse_locations_page)

    async def parse_locations_page(self, response: Response) -> AsyncIterator[Request]:
        self.cards = {}
        for card in response.css("div.card"):
            if lid := card.xpath('.//div[starts-with(@id, "s-lc-whw")]/@id').get():
                self.cards[lid.removeprefix("s-lc-whw")] = card
        async for request in super().start():
            yield request

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs
    ) -> Iterable[Feature | Request]:
        name = item.pop("name") or ""
        # LibCal also lists departments, services, kiosks, a holds locker,
        # a duplicate Scenic Woods and a TECHLink lab inside Vinson, none of
        # which are on the locations page.
        if (card := self.cards.get(str(item["ref"]))) is None:
            return
        if name.startswith(("Barbara Bush Literacy Plaza", "BOOKLink", "Freedmen")):
            # A plaza outside the Central Library, a book vending kiosk and a
            # heritage visitor center.
            return
        if name.startswith("TECHLink") and name != "TECHLink Dixon":
            # Makerspaces inside a branch, sharing its address. Dixon is a
            # former branch library converted to a standalone TECHLink.
            return

        if name == "Central Campus":
            name = card.xpath('.//div[contains(@class, "header3")]').xpath("normalize-space(string(.))").get()
        item["name"] = name
        branch = name.removesuffix(" Neighborhood Library").removesuffix(" Regional Library")
        if branch != name:
            item["branch"] = branch

        address = card.xpath('.//a[contains(@href, "google.com/maps")]').xpath("normalize-space(string(.))").get()
        if match := ADDRESS_REGEX.match(address or ""):
            item["street_address"], item["city"], item["state"], item["postcode"] = match.groups()
        else:
            item["addr_full"] = address
        if phone := card.xpath('.//a[starts-with(@href, "tel:")]/@href').get():
            item["phone"] = phone.removeprefix("tel:")
        item["image"] = card.xpath(".//img/@src").get()

        if Selector(text=location.get("desc") or "<html/>").css(".icon-accessible"):
            apply_yes_no(Extras.WHEELCHAIR, item, True)

        yield item
