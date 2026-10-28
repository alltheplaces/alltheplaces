import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy import Request, Spider
from scrapy.http import Response
from twisted.python.failure import Failure

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours, day_range, sanitise_day
from locations.items import Feature

LOCATOR = "https://communitymarkets.com/wp-admin/admin-ajax.php?action=asl_load_stores"
SITEMAP = "https://communitymarkets.com/page-sitemap.xml"

DAY = "|".join(DAYS_FULL) + r"|Mon|Tues?|Wed|Thur?s?|Fri|Sat|Sun"
TIME = r"\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?"
# "Mon - Sat: 6am -10pm", "Everyday: 7am - 9pm"
HOURS = re.compile(
    rf"(?:(?P<daily>every\s*day|daily)|(?P<days>(?:{DAY})(?:\s*(?P<joiner>[-–]|&|and|to)\s*(?:{DAY}))?))"
    rf"\s*:?\s*(?P<opens>{TIME})\s*[-–]\s*(?P<closes>{TIME})",
    re.IGNORECASE,
)
# "13710 Deshler Road,North Baltimore, OH 45872"
ADDRESS = re.compile(r"^(?P<street>.+?),\s*(?P<city>[^,]+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})")
# A store's pharmacy counter has a page of its own, which repeats the store's address.
NOT_A_STORE = re.compile(r"-pharmacy/?$|/tailgating-recipes/", re.IGNORECASE)
BANNERS = ("Great Scot", "Sack 'N Save")


class CommunityMarketsUSSpider(Spider):
    """Neither of the two things this site publishes about its stores is enough alone.

    The store locator states 13 stores, with the only coordinates published anywhere,
    but its hours are the store locator plugin's untouched default: every one of the
    13 claims to open 9:30am to 6:30pm every day of the week, where their own pages
    say 6am to 10pm.

    The site's page list, meanwhile, has a page for each of those 13 and for four more
    the locator never mentions, among them every Great Scot store. Those pages state
    the hours a store really keeps.

    So the pages are read for hours, the locator is read for everything else, and the
    two are matched on the slug a store's page is at, which the locator repeats in
    front of its own. A page is only believed about which store it is when no locator
    store claims it: three of them link a map of another town's address entirely.
    """

    name = "community_markets_us"
    # The stores trade under several banners, none of which has a Wikidata item of its
    # own. PCC Community Markets, which does, is a different chain altogether.
    item_attributes = {"operator": "Community Markets"}
    start_urls = [SITEMAP]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages: dict[str, dict] = {}
        self.pending = 0

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        urls = [
            url for url in re.findall(r"<loc>(?:<!\[CDATA\[)?([^<\]]+)", response.text) if not NOT_A_STORE.search(url)
        ]
        self.pending = len(urls)
        for url in urls:
            # Every one of these has to come back, answered or failed, for the locator
            # to be asked for at all; one page redirects onto another, and filtering
            # that as a duplicate would leave the count short and the run empty.
            yield Request(url, callback=self.parse_page, errback=self.page_failed, dont_filter=True)

    def parse_page(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        # A store's page states its hours under a heading, and usually links a map of
        # its address; one store's page links no map, so either marks a store's page.
        link = response.xpath('//a[contains(@href, "maps/dir")]/@href').re_first(r"maps/dir//(.+)$")
        hours = self.stated_hours(response)
        if link or hours:
            slug = response.url.rstrip("/").rsplit("/", 1)[-1]
            self.pages[slug] = {
                "url": response.url,
                "name": response.xpath("normalize-space(//h1)").get(),
                "address": unquote(link).replace("+", " ").strip() if link else "",
                # "Phone:" and the number it labels are separate text nodes, so the
                # page's text is joined before it is looked for.
                "phone": self.stated_phone(response),
                "hours": hours,
            }
        yield from self.done()

    def page_failed(self, failure: Failure) -> Iterable[Request]:
        self.logger.warning(f"No page at {failure.request.url}: {failure.value}")
        yield from self.done()

    def done(self) -> Iterable[Request]:
        """Ask for the locator once every page has been read."""
        self.pending -= 1
        if self.pending == 0:
            yield Request(LOCATOR, callback=self.parse_locator)

    def parse_locator(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        claimed = set()
        for store in response.json():
            item = Feature()
            item["ref"] = store.get("id")
            self.name_and_brand(item, store.get("title"))
            item["street_address"] = store.get("street")
            item["city"] = store.get("city")
            item["state"] = store.get("state")
            item["postcode"] = store.get("postal_code")
            item["phone"] = store.get("phone")
            item["lat"] = store.get("lat")
            item["lon"] = store.get("lng")

            # The locator repeats a store's page slug in front of its own, so
            # "ada-ada" is the store whose page is at /ada/.
            if page := self.page_for(store.get("slug"), claimed):
                item["website"] = page["url"]
                item["opening_hours"] = self.hours(page["hours"])
            else:
                self.logger.info(f"No page found for {store.get('slug')!r}, so no hours for it")

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

        # Whatever is left is a store the locator does not mention.
        for slug, page in self.pages.items():
            if slug in claimed:
                continue
            if not (address := ADDRESS.match(page["address"])):
                continue
            town = re.sub(r"[^a-z]", "", address["city"].casefold())
            if town and town not in re.sub(r"[^a-z]", "", slug.casefold()):
                self.logger.warning(f"{slug} links an address in {address['city']!r}, so it is not read")
                continue

            item = Feature()
            item["ref"] = slug
            self.name_and_brand(item, page["name"])
            item["street_address"] = address["street"]
            item["city"] = address["city"]
            item["state"] = address["state"]
            item["postcode"] = address["postcode"]
            item["phone"] = page["phone"]
            item["website"] = page["url"]
            item["opening_hours"] = self.hours(page["hours"])
            # No coordinates are published for these: only the locator states any.
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

    def page_for(self, slug: str | None, claimed: set) -> dict | None:
        for page_slug, page in self.pages.items():
            if (slug or "").startswith(f"{page_slug}-"):
                claimed.add(page_slug)
                return page
        return None

    @staticmethod
    def stated_phone(response: Response) -> str | None:
        """Return the store's own number, which is labelled, and not the pharmacy's."""
        text = re.sub(r"\s+", " ", " ".join(response.xpath("//body//text()").getall()))
        if match := re.search(r"(?<!Pharmacy )Phone:\s*(\(?\d{3}\)?[ .-]?\d{3}[.-]\d{4})", text):
            return match.group(1)
        return None

    @staticmethod
    def stated_hours(response: Response) -> str:
        """Return the hours a heading introduces, which a pharmacy counter's are not.

        What follows the heading is a paragraph on most pages and a heading of its own
        on others, so the hours are read up to the heading that starts the next
        section. Those headings name themselves with a colon, where an hours line such
        as "Everyday: 7am - 9pm" carries its colon in the middle.
        """
        for heading in response.xpath("//h2[contains(., 'Hours')]"):
            if "pharmacy" in (heading.xpath("normalize-space(.)").get() or "").casefold():
                continue
            lines = []
            for sibling in heading.xpath("following-sibling::*"):
                text = re.sub(r"\s+", " ", sibling.xpath("normalize-space(.)").get() or "").strip()
                if sibling.root.tag in ("h1", "h2") and text.endswith(":"):
                    break
                lines.append(text)
            return " ".join(lines)
        return ""

    def name_and_brand(self, item: Feature, title: str | None) -> None:
        title = re.sub(r"\s+", " ", (title or "").replace("‘", "'").replace("’", "'")).strip()
        for banner in BANNERS:
            if title.casefold().startswith(banner.casefold()):
                item["brand"] = banner
                item["branch"] = title[len(banner) :].strip(" -–") or None
                return
        item["brand"] = "Community Markets"
        item["branch"] = title or None

    def hours(self, text: str) -> OpeningHours:
        """Read hours such as "Mon - Sat: 6am -10pm Sun: 7am - 10pm"."""
        oh = OpeningHours()
        for match in HOURS.finditer(text or ""):
            if match["daily"]:
                days = list(DAYS_FULL)
            else:
                found = [sanitise_day(part) for part in re.split(r"\s*(?:[-–]|&|and|to)\s*", match["days"])]
                days = [day for day in found if day]
                if len(days) == 2 and (match["joiner"] or "").strip() in ("-", "–", "to"):
                    days = day_range(*days)
            for day in days:
                oh.add_range(day, self.normalise(match["opens"]), self.normalise(match["closes"]))
        if text and not oh:
            self.logger.warning(f"Unparsed hours: {text[:120]!r}")
        return oh

    @staticmethod
    def normalise(time: str) -> str:
        time = re.sub(r"[\s.]", "", time).upper()
        hour, _, rest = time.partition(":")
        if not rest:
            return f"{int(hour[:-2]) % 12 + (12 if hour.endswith('PM') else 0):02d}:00"
        return f"{int(hour) % 12 + (12 if rest.endswith('PM') else 0):02d}:{rest[:2]}"
