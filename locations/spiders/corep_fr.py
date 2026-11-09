import re
from typing import Any

from chompjs import parse_js_object
from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CorepFRSpider(SitemapSpider):
    name = "corep_fr"
    item_attributes = {"brand": "Corep", "brand_wikidata": "Q73111125", "name": "Corep"}
    sitemap_urls = ["https://www.corep.fr/sitemap.xml"]
    sitemap_rules = [(r"/fr/agence/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = response.xpath('//script/text()[contains(., "var locations")]').get("")
        if "var locations" not in script:
            return
        # [name, map popup HTML, lat, lon, id]
        name, popup, lat, lon, ref = parse_js_object(script.split("var locations", 1)[1])[0]

        item = Feature()
        item["ref"] = str(ref)
        item["website"] = response.url
        item["branch"] = name.removeprefix("Corep ")
        item["lat"] = lat
        item["lon"] = lon

        lines = [line.strip() for line in Selector(text=popup).xpath("//p/text()").getall() if line.strip()]
        for index, line in enumerate(lines):
            if match := re.match(r"(\d{5})\s+(.+)", line):
                item["postcode"], item["city"] = match.groups()
                item["street_address"] = merge_address_lines(lines[:index])
                item["phone"] = "; ".join(lines[index + 1 :])
                break

        item["email"] = response.css(".agence a[href^='mailto:']::attr(href)").get("")

        hours = []
        # A separate "Horaires exceptionnels" block holds temporary hours.
        for line in response.xpath('//h2[contains(., "Horaires d\'ouverture")]/following-sibling::ul[1]/li'):
            text = line.xpath("normalize-space()").get("").replace("\xa0", " ").split(">")[0]
            text = re.sub(r"&?\s*Jours fériés", "", text)
            text = re.sub(r"(\d{1,2})h(\d{2})?", lambda m: f"{m[1]}:{m[2] or '00'}", text)
            hours.append(text.replace(" de ", " ").replace(" puis ", ", "))
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            "; ".join(hours), days=DAYS_FR, delimiters=DELIMITERS_FR + ["et"], closed=CLOSED_FR
        )

        apply_category(Categories.SHOP_COPYSHOP, item)

        yield item
