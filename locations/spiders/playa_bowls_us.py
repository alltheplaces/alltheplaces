import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.linked_data_parser import LinkedDataParser


class PlayaBowlsUSSpider(SitemapSpider):
    name = "playa_bowls_us"
    item_attributes = {"brand": "Playa Bowls", "brand_wikidata": "Q114618507"}
    sitemap_urls = ["https://playabowls.com/sitemap.xml"]
    sitemap_rules = [("/location/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        ld_data = json.loads(
            re.sub(
                r'([}\]"])\s*(?=")',  # end of value followed by next key
                r"\1,",
                (response.xpath('//*[@type="application/ld+json"]//text()').get().strip()),
            )
        )
        item = LinkedDataParser.parse_ld(ld_data)
        item["ref"] = response.url.split("/")[-1]
        item["branch"] = item.pop("name").replace("Playa Bowls - ", "")
        oh = OpeningHours()
        try:
            if "Open Everyday " in ld_data.get("openingHours"):
                for day in DAYS_FULL:
                    open_time, close_time = ld_data.get("openingHours").replace("Open Everyday ", "").split("-")
                    oh.add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I%p"
                    )
            else:
                oh.add_ranges_from_string(ld_data["openingHours"])
        except:
            pass
        item["opening_hours"] = oh
        apply_category(Categories.FAST_FOOD, item)

        yield item
