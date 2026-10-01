import json
import re
from typing import Any, Iterable
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT

# GameStop's store locator requires searching by postal code with a maximum
# radius of 200 miles (responses above 200 miles can exceed 3MB response limits).
# To achieve 100% US coverage while minimizing API volume (~638 requests),
# this spider samples consolidated postal regions with population >= 50,000
# supplemented with targeted rural/isolated hubs (AK, ND, SD, MT, Upper MI).
GAMESTOP_SHARED_ATTRIBUTES = {
    "brand": "GameStop",
    "brand_wikidata": "Q202210",
    "extras": Categories.SHOP_VIDEO_GAMES.value,
}


class GamestopUSSpider(Spider):
    name = "gamestop_us"
    item_attributes = GAMESTOP_SHARED_ATTRIBUTES
    allowed_domains = ["www.gamestop.com"]
    _base_url = "https://www.gamestop.com/on/demandware.store/Sites-gamestop-us-Site/default/Stores-FindStores"
    _query_params = {
        "hasCondition": "false",
        "hasVariantsAvailableForLookup": "false",
        "hasVariantsAvailableForPickup": "false",
        "source": "plp",
        "showMap": "false",
        "products": "undefined:1",
    }
    start_urls = [f"{_base_url}?{urlencode(_query_params, safe=':')}"]
    requires_proxy = "US"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1.0,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504, 522, 524, 408],
    }
    seen_refs: set[str] = set()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.seen_refs = set()

    # Supplemental postal codes for isolated areas >200 miles from any 50k+ city
    # (Alaska, rural Northern Plains, and Upper Michigan) to achieve 100% US coverage
    # without inflating the nationwide population threshold.
    SUPPLEMENTAL_POSTAL_REGIONS = [
        "99504",  # Anchorage & Wasilla, AK
        "99701",  # Fairbanks, AK
        "58501",  # Bismarck, ND
        "58701",  # Minot & Williston, ND
        "58201",  # Grand Forks, ND
        "57701",  # Rapid City, SD
        "59102",  # Billings, MT
        "59718",  # Bozeman, MT
        "49855",  # Marquette, MI (Upper Peninsula)
    ]

    @classmethod
    def get_postal_regions(cls) -> Iterable[str]:
        """
        Yield all postal codes required for 100% US coverage with a 200-mile search radius.
        Combines 50k+ population centers with targeted rural/isolated hubs.
        """
        seen = set()
        for region in postal_regions("US", min_population=50000, consolidate_cities=True):
            code = str(region["postal_region"])
            seen.add(code)
            yield code

        for code in cls.SUPPLEMENTAL_POSTAL_REGIONS:
            if code not in seen:
                seen.add(code)
                yield code

    def start_requests(self) -> Iterable[FormRequest]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://www.gamestop.com/stores/",
            "X-Requested-With": "XMLHttpRequest",
        }
        for url in self.start_urls:
            for postcode in self.get_postal_regions():
                yield FormRequest(
                    url=url,
                    method="POST",
                    headers=headers,
                    formdata={"postalCode": postcode, "radius": "200", "csrf_token": "0"},
                )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("stores", []):
            ref = str(location.get("ID", ""))
            if not ref or ref in self.seen_refs:
                continue
            self.seen_refs.add(ref)

            item = DictParser.parse(location)
            item["name"] = re.sub(r"(?i)\s*-\s*gamestop\b", "", item["name"]).strip()
            if location.get("address2"):
                suite = location.get("address2").upper().replace("STE", "Suite")
                item["street_address"] = clean_address([location.get("address1"), suite])
            item["website"] = "https://www.gamestop.com/search/?store=" + item["ref"]
            if hours_raw := location.get("storeOperationHours"):
                try:
                    hours_data = json.loads(hours_raw)
                    if all(day.get("open") == "CLOSED" and day.get("close") == "CLOSED" for day in hours_data):
                        set_closed(item)
                    else:
                        item["opening_hours"] = OpeningHours()
                        for day_hours in hours_data:
                            item["opening_hours"].add_range(
                                day_hours["day"], day_hours["open"], day_hours["close"], "%H%M"
                            )
                except Exception:
                    pass

            yield item
