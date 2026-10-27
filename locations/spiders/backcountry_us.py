import json
import random
import re
from typing import Any, AsyncIterator, Iterable

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Request, Response
from scrapy.settings.default_settings import RETRY_EXCEPTIONS
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# Every URL here is first served an AWS WAF challenge that resolves itself via
# JS and reloads; wait for that instead of trusting the first response.
WAIT_FOR_WAF_CHALLENGE = PageMethod(
    "wait_for_function",
    "() => !document.documentElement.outerHTML.includes('AwsWafIntegration')",
    timeout=20000,
)

CAMOUFOX_SETTINGS_FOR_AWS_WAF = DEFAULT_CAMOUFOX_SETTINGS | {
    # Default blocks everything but the document, including the WAF's own challenge.js.
    "CAMOUFOX_ABORT_REQUEST": lambda request: not request.resource_type == "document"
    and not (request.resource_type in ["script", "xhr", "fetch"] and ".awswaf.com" in request.url),
    # Concurrent challenge-solving above this starts timing out.
    "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    # WAF challenge timeouts aren't retried by default.
    "RETRY_EXCEPTIONS": RETRY_EXCEPTIONS + [PlaywrightTimeoutError],
}

# "2650 NE University Village St., Seattle, WA. 98105" or
# "650A Stanford Shopping Center, Palo Alto, CA 94304 | (650) 382-0230"
ADDRESS = re.compile(
    r"^(?P<street>.+?),\s*(?P<city>[^,]+?),\s*(?P<state>[A-Z]{2})\.?\s+(?P<postcode>\d{5})(?:\s*\|\s*(?P<phone>.+))?$"
)
PHONE = re.compile(r"^(?:Phone:\s*)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4})$")
HOURS = re.compile(r"^(?:REGULAR HOURS:\s*)?((?:Mon|Sun)\w*\W.*\d\s*[ap]m.*)$", re.IGNORECASE)


class BackcountryUSSpider(CamoufoxSpider):
    """Backcountry's retail and outlet stores, from its Contentstack-built pages.

    Every page is behind an AWS WAF challenge, which Camoufox lets resolve
    itself. The pages carry no coordinates or structured
    data, only free-text address, phone and hours paragraphs.
    """

    name = "backcountry_us"
    item_attributes = {"brand": "Backcountry", "brand_wikidata": "Q4839592", "name": "Backcountry"}
    start_urls = ["https://www.backcountry.com/info/retail-stores"]
    custom_settings = CAMOUFOX_SETTINGS_FOR_AWS_WAF

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield self.waf_request(url, self.parse)

    @staticmethod
    def waf_request(url: str, callback) -> Request:
        return Request(url, callback=callback, meta={"camoufox_page_methods": [WAIT_FOR_WAF_CHALLENGE]})

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature | Request]:
        if (cms_data := self.cms_data(response)) is None:
            yield from self.retry(response)
            return
        for card in self.cards(cms_data):
            link = card.get("link") or ""
            if "/retail-store-" in link:
                yield self.waf_request(response.urljoin(link), self.parse_store)
            elif "Outlet" in (card.get("tracking") or {}).get("name", ""):
                lines = self.text_lines(card.get("text"))
                if item := self.parse_lines(lines):
                    item["branch"] = lines[0].split(" - ")[0]
                    item["name"] = "Backcountry Outlet"
                    item["ref"] = f"outlet-{item['branch'].lower().replace(' ', '-')}"
                    item["website"] = response.url
                    yield item

    def parse_store(self, response: Response) -> Iterable[Feature | Request]:
        if (cms_data := self.cms_data(response)) is None:
            yield from self.retry(response)
            return
        if item := self.parse_lines(self.text_lines(cms_data)):
            item["ref"] = response.url.rstrip("/").rsplit("/retail-store-", 1)[1]
            item["branch"] = response.xpath("//title/text()").get("").split(" Retail Store")[0].strip()
            item["website"] = response.url
            yield item

    def parse_lines(self, lines: list[str]) -> Feature | None:
        item = Feature()
        for line in lines:
            if "street_address" not in item and (address := ADDRESS.match(line)):
                item["street_address"] = address["street"]
                item["city"] = address["city"]
                item["state"] = address["state"]
                item["postcode"] = address["postcode"]
                if address["phone"]:
                    item["phone"] = address["phone"]
            elif "phone" not in item and (phone := PHONE.match(line)):
                item["phone"] = phone[1]
            elif hours := HOURS.match(line):
                item.setdefault("opening_hours", OpeningHours()).add_ranges_from_string(hours[1])
        if "street_address" not in item:
            return None
        apply_category(Categories.SHOP_OUTDOOR, item)
        return item

    @staticmethod
    def cms_data(response: Response) -> Any:
        try:
            next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
            return next_data["props"]["pageProps"]["cmsData"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def retry(self, response: Response) -> Iterable[Request]:
        # A settled render occasionally still lacks the CMS payload.
        if response.request is not None:
            if retry := get_retry_request(
                response.request, spider=self, reason="no CMS data found", priority_adjust=random.randint(-20, -1)
            ):
                yield retry

    @classmethod
    def cards(cls, node: Any) -> Iterable[dict]:
        if isinstance(node, dict):
            if node.get("__typename") == "Card":
                yield node
            for value in node.values():
                yield from cls.cards(value)
        elif isinstance(node, list):
            for value in node:
                yield from cls.cards(value)

    @classmethod
    def text_lines(cls, node: Any) -> list[str]:
        """Each rich-text paragraph's text, in page order."""
        lines = []
        if isinstance(node, dict):
            if node.get("type") in ("p", "h1", "h2", "h3"):
                text = "".join(cls.leaf_texts(node)).replace("\u00a0", " ").replace("\u2028", " ").strip()
                if text:
                    lines.append(text)
            else:
                for value in node.values():
                    lines.extend(cls.text_lines(value))
        elif isinstance(node, list):
            for value in node:
                lines.extend(cls.text_lines(value))
        return lines

    @classmethod
    def leaf_texts(cls, node: Any) -> Iterable[str]:
        if isinstance(node, dict):
            if isinstance(node.get("text"), str):
                yield node["text"]
            for value in node.get("children", []):
                yield from cls.leaf_texts(value)
