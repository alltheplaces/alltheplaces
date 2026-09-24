import re
from typing import AsyncIterator, Iterable

from scrapy.http import Request, Response, TextResponse

from locations.items import Feature
from locations.storefinders.lib_cal import LibCalSpider

POSTCODE_REGEX = re.compile(r"\b(NJ)\s+(\d{5}(?:-\d{4})?)$")
NAMES = {
    "Headquarters, Manalapan": ("Monmouth County Library Headquarters", "Headquarters"),
    "Eastern Branch, Shrewsbury": ("Monmouth County Library Eastern Branch", "Eastern Branch"),
}


class MonmouthCountyLibraryUSSpider(LibCalSpider):
    name = "monmouth_county_library_us"
    item_attributes = {"operator": "Monmouth County Library", "operator_wikidata": "Q6901077"}
    libcal_host = "monmouthcountylib.libcal.com"
    libcal_iid = 6730
    country = "US"

    async def start(self) -> AsyncIterator[Request]:
        # LibCal has hours and a branch URL but no address, so the site's
        # "Our Branches" menu, which gives each branch's address and main
        # number, is read first.
        yield Request("https://monmouthcountylib.org/library-branches/", callback=self.parse_branch_menu)

    async def parse_branch_menu(self, response: Response) -> AsyncIterator[Request]:
        self.branches = {}
        for entry in response.xpath(
            '//li[div[contains(@class, "ubermenu-content-block")]//a[starts-with(@href, "tel:")]]'
        ):
            url = entry.xpath("./a/@href").get().strip().rstrip("/")
            self.branches[url] = entry.css(".ubermenu-content-block")
        async for request in super().start():
            yield request

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # The LibCal contact field is a staff directory with extensions, not
        # the branch's own number.
        location["contact"] = ""

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs
    ) -> Iterable[Feature | Request]:
        label = item.pop("name")
        item["name"], item["branch"] = NAMES.get(label, ("{} Library".format(label), label))

        if block := self.branches.get((item["website"] or "").rstrip("/")):
            # The address link is a Google Maps link, except Ocean Township's,
            # whose href is the address as plain text.
            item["addr_full"] = block.xpath('normalize-space(.//a[not(starts-with(@href, "tel:"))])').get()
            if m := POSTCODE_REGEX.search(item["addr_full"]):
                item["state"], item["postcode"] = m.groups()
            # The link text is used as Marlboro's tel: link lacks the area code.
            item["phone"] = (
                block.xpath('normalize-space(.//a[starts-with(@href, "tel:")])').get().removeprefix("Main number:")
            )
        else:
            self.logger.warning("No address found for %s", item["name"])
        yield item
