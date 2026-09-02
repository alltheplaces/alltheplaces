import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class BenitaBGSpider(Spider):
    name = "benita_bg"
    item_attributes = {"brand": "Бенита", "brand_wikidata": "Q111762601", "name": "Бенита", "country": "BG"}
    start_urls = ["https://benita.bg/бензиностанции"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.css("div.object_item"):
            item = Feature()
            item["lat"] = location.attrib.get("data-lat")
            item["lon"] = location.attrib.get("data-lng")
            item["website"] = location.css("a.pull-left::attr(href)").get()
            item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]

            name = location.css("a.pull-left h2::text").get("").strip()
            item["branch"] = re.sub(r"(?i)^benita\s*", "", name).strip(" –-")

            item["addr_full"] = location.css("span.short_description::text").get("").strip()
            item["phone"] = location.css('a.link[href^="tel:"]::attr(href)').get("").removeprefix("tel:")
            item["email"] = location.css('a.link[href^="mailto:"]::attr(href)').get("").removeprefix("mailto:")

            filters = [f.upper() for f in location.css("div.object_filter::text").getall()]

            apply_yes_no(Fuel.DIESEL, item, any("DIESEL" in f for f in filters))
            apply_yes_no(Fuel.OCTANE_95, item, any("A95" in f for f in filters))
            apply_yes_no(Fuel.OCTANE_100, item, any("A100" in f for f in filters))
            apply_yes_no(Fuel.LPG, item, any("LPG" in f for f in filters))
            apply_yes_no(Fuel.PROPANE, item, any("БИТОВА ГАЗ" in f for f in filters))
            apply_yes_no(Fuel.CNG, item, any("CNG" in f for f in filters))
            apply_yes_no(Fuel.ADBLUE, item, any("ADBLUE" in f for f in filters))
            apply_yes_no(Extras.CAR_WASH, item, any("АВТОМИВКА" in f for f in filters))

            apply_category(Categories.FUEL_STATION, item)

            yield item
