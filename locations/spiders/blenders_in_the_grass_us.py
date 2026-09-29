import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class BlendersInTheGrassUSSpider(Spider):
    name = "blenders_in_the_grass_us"
    item_attributes = {"brand": "Blenders in the Grass"}
    start_urls = ["https://www.drinkblenders.com/blendersland/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    city_overrides = {
        "Oxnard Shores": "Oxnard",
        "South Oxnard": "Oxnard",
        "Las Posas Plaza": "Camarillo",
        "Village Square": "Camarillo",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = response.xpath('//*[@id="pg-126-2" or @id="pg-126-3"]//h4[normalize-space()]')
        for location in locations:
            branch = location.xpath("normalize-space()").get()
            details = location.xpath("following-sibling::p[1]")
            lines = [text.strip() for text in details.xpath(".//text()").getall() if text.strip()]

            if lines[0].startswith("("):
                city = lines.pop(0).strip("()")
            else:
                city = self.city_overrides.get(branch, branch)

            phone = details.css("strong::text").re_first(r"\(?\d{3}\)?[\s-]+\d{3}-\d{4}")
            item = Feature(
                ref=re.sub(r"\D", "", phone),
                branch=branch,
                street_address=lines[0],
                city=city,
                state="CA",
                country="US",
                phone=phone,
                website=response.url,
            )

            hours_text = details.xpath("string()").re_first(r"M-F.+")
            hours_text = hours_text.replace("M-F", "Mo-Fr").replace("Sa/Su", "Sa-Su")
            hours_text = re.sub(r"(\d)([ap])\b", lambda match: f"{match[1]}{match[2].upper()}M", hours_text)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "juice"
            yield item
