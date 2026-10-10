import json
import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


def clean(value: str | None) -> str | None:
    value = (value or "").strip(" ,-")
    if value.lower().startswith("test"):
        return None  # placeholder such as "Test Number"
    return value or None


class MyanmarPostMmSpider(Spider):
    name = "myanmar_post_mm"
    item_attributes = {"operator": "မြန်မာ့စာတိုက်", "operator_wikidata": "Q65335968"}
    allowed_domains = ["myanmarpost.com.mm"]
    start_urls = ["https://myanmarpost.com.mm/post-offices?tab=office&page=1"]
    # Non-browser user agents are served the mobile postcode search page, which lacks the office list.
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Laravel + Inertia.js: the page props (a paginated office list, 30 per page) are embedded as JSON.
        offices = json.loads(response.xpath("//@data-page").get())["props"]["offices"]
        if offices["meta"]["current_page"] == 1:
            for page in range(2, offices["meta"]["last_page"] + 1):
                yield Request(url=f"https://myanmarpost.com.mm/post-offices?tab=office&page={page}")

        for office in offices["data"]:
            if not office["status"] or office["deleted"]:
                continue
            item = Feature()
            item["ref"] = str(office["id"])
            # e.g. "Kyauktan Post Office (Taunggyi)", "Htonaing Postoffice", "Myaing Gyi Ngu Postcoffie"
            name = re.sub(r"\s*Post\s*c?off(?:ice|ie)\b", " ", office["name_en"], flags=re.IGNORECASE)
            item["branch"] = re.sub(r"\s+", " ", name).strip()
            item["extras"]["branch:my"] = re.sub(r"\s*စာတိုက်$", "", (office["name_mm"] or "").strip()) or None
            item["lat"], item["lon"] = office["latitude"], office["longitude"]
            # "no_en" holds house numbers but also placeholders ("-", "Test Number") and village names.
            item["street_address"] = ", ".join(
                filter(None, (clean(office[key]) for key in ("no_en", "street_en", "quarter_en")))
            )
            item["city"] = (office.get("town") or {}).get("name_en")
            item["state"] = (office.get("region") or {}).get("name_en")
            item["postcode"] = office["postcode"]
            apply_category(Categories.POST_OFFICE, item)
            yield item
