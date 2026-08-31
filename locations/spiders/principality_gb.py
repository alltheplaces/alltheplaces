import json
import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# UK postcode pattern
POSTCODE_RE = re.compile(r"([A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][ABD-HJLNP-UW-Z]{2})$")


class PrincipalityGBSpider(Spider):
    """Principality Building Society branches in Great Britain.

    The branch-finder page embeds a JSON blob with all 68 branches including
    coordinates, a partial address, and a URL to each branch's detail page.
    Each detail page contains structured opening hours in a <dl> element.
    """

    name = "principality_gb"
    item_attributes = {
        "brand": "Principality Building Society",
        "brand_wikidata": "Q7245099",
    }
    allowed_domains = ["www.principality.co.uk"]
    start_urls = ["https://www.principality.co.uk/branch-finder"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url, callback=self.parse_branch_list)

    def parse_branch_list(self, response: Response, **kwargs: Any) -> Any:
        raw = response.xpath('//script[@id="branches-data"]/text()').get()
        if not raw:
            return
        data = json.loads(raw)
        for branch in data.get("branches", []):
            detail_url = "https://www.principality.co.uk" + branch["detailsUrl"]
            yield Request(
                detail_url,
                callback=self.parse_branch,
                cb_kwargs={"branch": branch},
            )

    def parse_branch(self, response: Response, branch: dict, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = str(branch["branchId"])
        item["name"] = branch["name"]
        item["lat"] = branch["position"]["lat"]
        item["lon"] = branch["position"]["lng"]
        item["website"] = response.url
        item["country"] = "GB"

        # Parse address: last comma-part is always the UK postcode,
        # second-to-last is typically the city/region.
        address = branch.get("address", "")
        parts = [p.strip() for p in address.split(",") if p.strip()]
        if parts:
            postcode_match = POSTCODE_RE.search(address)
            item["postcode"] = postcode_match.group(1) if postcode_match else None
            # Remove postcode from parts to identify city
            addr_parts = [p for p in parts if not POSTCODE_RE.fullmatch(p.strip())]
            if len(addr_parts) >= 2:
                item["city"] = addr_parts[-1]
                item["street_address"] = ", ".join(addr_parts[:-1])
            elif addr_parts:
                item["street_address"] = addr_parts[0]

        # Parse opening hours from the <dl> element on the detail page
        oh = OpeningHours()
        for div in response.xpath("//dl/div"):
            day = div.xpath("dt/text()").get("").strip()
            hours = div.xpath("dd/text()").get("").strip()
            if day and hours and hours.lower() != "closed":
                oh.add_ranges_from_string(f"{day} {hours}")
        item["opening_hours"] = oh

        apply_category(Categories.BANK, item)

        yield item
