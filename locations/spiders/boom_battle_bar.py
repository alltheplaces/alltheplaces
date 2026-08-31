import json
import re
from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BoomBattleBarSpider(StructuredDataSpider):
    name = "boom_battle_bar"
    item_attributes = {"brand": "Boom Battle Bar", "brand_wikidata": "Q113503635"}
    # The main UK locations page - regions JSON is embedded in the page HTML
    start_urls = ["https://boombattlebar.com/uk/"]
    wanted_types = ["BarOrPub", "EntertainmentBusiness"]
    search_for_twitter = False

    COUNTRY_MAP = {"uk": "GB", "ie": "IE", "us": "US", "au": "AU"}

    def parse(self, response: Response, **kwargs):
        # Location list is embedded as JSON in :sync-regions attribute of <location-accordion>
        m = re.search(r':sync-regions="(\[.*?\])"', response.text, re.DOTALL)
        if not m:
            self.logger.error("Could not find :sync-regions data on %s", response.url)
            return

        regions_raw = m.group(1).replace("&quot;", '"')
        regions = json.loads(regions_raw)

        for region in regions:
            for country in region.get("countries", []):
                country_code = self.COUNTRY_MAP.get(country.get("slug", "").lower(), "")
                for location in country.get("locations", []):
                    if location.get("is_coming_soon"):
                        continue
                    url = location.get("url", "").rstrip("/") + "/"
                    if not url.startswith("http"):
                        continue
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_sd,
                        meta={
                            "country_code": country_code,
                            "blog_id": location.get("blog_id"),
                        },
                    )

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        country_code = response.meta.get("country_code", "")
        blog_id = response.meta.get("blog_id")

        # Use the blog_id as a stable ref
        item["ref"] = blog_id or response.url

        # The name includes the brand name + location; put the location part in branch
        name = item.get("name", "")
        if name.startswith("Boom Battle Bar "):
            item["branch"] = name.removeprefix("Boom Battle Bar ")
            del item["name"]

        if country_code:
            item["country"] = country_code

        item["website"] = response.url

        apply_category(Categories.BAR, item)

        yield item
