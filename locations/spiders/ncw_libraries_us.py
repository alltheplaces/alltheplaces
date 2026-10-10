import re
from typing import Any, AsyncIterator, Iterable

from scrapy.http import Request, Response, TextResponse
from twisted.python.failure import Failure

from locations.items import Feature
from locations.storefinders.lib_cal import LibCalSpider

LOCATIONS_URL = "https://www.ncwlibraries.org/locations/"
BRANCH_PAGE_REGEX = re.compile(r"(?:https?://www\.ncwlibraries\.org)?/locations/([^/]+)/")
# e.g. "108 S 3rd Street Brewster, WA 98812", "218 West Main Street, Coulee
# City, WA 99115", with the town filled in from the branch name.
ADDRESS_TEMPLATE = r"(\d+.*?),?\s*{},\s*([A-Z]{{2}})\s+(\d{{5}})"


class NcwLibrariesUSSpider(LibCalSpider):
    name = "ncw_libraries_us"
    item_attributes = {"operator": "NCW Libraries", "operator_wikidata": "Q7054759"}
    libcal_host = "ncwlibraries.libcal.com"
    libcal_iid = 6523
    country = "US"

    async def start(self) -> AsyncIterator[Request]:
        yield Request(LOCATIONS_URL, callback=self.parse_locations)

    async def parse_locations(self, response: Response) -> AsyncIterator[Request]:
        # LibCal holds names and hours only, so the branch pages supply
        # everything else. They are keyed on the town in their URL, which is
        # how a LibCal location is named too.
        self.branch_pages = {}
        for href in response.css("a::attr(href)").getall():
            if m := BRANCH_PAGE_REGEX.fullmatch(href.strip()):
                town = m.group(1).removesuffix("-public-library").replace("-", " ")
                self.branch_pages[town] = response.urljoin(href)
        async for request in super().start():
            yield request

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs: Any
    ) -> Iterable[Request | Feature]:
        item["branch"] = item.pop("name").removesuffix(" Branch")
        item["name"] = "{} Public Library".format(item["branch"])
        if not (branch_page := self.branch_pages.get(item["branch"].lower())):
            self.logger.warning("No branch page found for %s", item["name"])
            yield item
            return
        item["website"] = branch_page
        yield Request(
            branch_page,
            callback=self.parse_branch_page,
            errback=self.parse_branch_page_error,
            cb_kwargs={"item": item},
        )

    def parse_branch_page(self, response: Response, item: Feature) -> Iterable[Feature]:
        contact = response.xpath('//*[@id="branch-contact"]//div[@class="et_pb_text_inner"]/p')
        # The accessibility plugin puts "opens phone dialer" and "create new
        # email" inside the links, so only text outside them is the address.
        address = re.sub(r"\s+", " ", " ".join(contact.xpath(".//text()[not(ancestor::a)]").getall()))
        if m := re.search(ADDRESS_TEMPLATE.format(re.escape(item["branch"])), address):
            item["street_address"], item["state"], item["postcode"] = m.groups()
            item["city"] = item["branch"]
        else:
            self.logger.warning("No address found for %s: %r", item["name"], address)
        if phone := contact.xpath('.//a[starts-with(@href, "tel:")]/@href').get():
            item["phone"] = phone.removeprefix("tel:").strip()
        if email := contact.xpath('.//a[starts-with(@href, "mailto:")]/@href').get():
            item["email"] = email.removeprefix("mailto:").strip()
        # A branch page's only location is a Google Maps embed, and its centre
        # sits about 190 m west of the building (up to 3 km where the map is
        # zoomed out), so it is not used as a coordinate source.
        yield item

    def parse_branch_page_error(self, failure: Failure) -> Iterable[Feature]:
        # Keep the location, without address and contact details, rather than
        # silently dropping it.
        request = failure.request  # ty: ignore[unresolved-attribute]
        self.logger.warning("Failed to fetch branch page %s: %r", request.url, failure.value)
        self.crawler.stats.inc_value(f"atp/{self.name}/branch_page_failed")
        yield request.cb_kwargs["item"]
