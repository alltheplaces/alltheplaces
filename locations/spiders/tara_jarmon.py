import re
from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.printemps import PrintempsSpider
from locations.user_agents import BROWSER_DEFAULT


class TaraJarmonSpider(XMLFeedSpider):
    name = "tara_jarmon"
    item_attributes = {"brand": "Tara Jarmon", "brand_wikidata": "Q141580805", "name": "Tara Jarmon"}
    allowed_domains = ["en.tarajarmon.com"]
    start_urls = ["https://en.tarajarmon.com/ajax_generate_xml_map.php"]
    itertag = "marqueur"
    # The bot user agent is redirected to google.com.
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    located_in_brands = {
        "GALERIES LAFAYETTE": {"brand": "Galeries Lafayette", "brand_wikidata": "Q3094686"},
        "PRINTEMPS": PrintempsSpider.item_attributes,
    }

    def parse_node(self, response: Response, selector: Selector) -> Any:
        item = Feature()
        item["ref"] = selector.xpath("@magasin_id").get()
        item["street_address"] = selector.xpath("@adresse").get()
        item["postcode"] = selector.xpath("@cp").get()
        item["city"] = selector.xpath("@ville").get()
        country = selector.xpath("@pays").get()
        # Monaco is listed under France.
        if item["postcode"] and item["postcode"].startswith("980"):
            country = "MC"
        item["country"] = {"Swiss": "CH"}.get(country, country)
        item["lat"] = selector.xpath("@lat").get()
        item["lon"] = selector.xpath("@lng").get()
        item["phone"] = selector.xpath("@telephone").get()
        item["email"] = selector.xpath("@email").get()
        if url := selector.xpath("@url").get():
            item["website"] = response.urljoin(url)

        branch = " ".join(selector.xpath("@nom").get("").split())
        for key, attributes in self.located_in_brands.items():
            if branch.upper().startswith(f"{key} "):
                item["located_in"] = attributes["brand"]
                item["located_in_wikidata"] = attributes["brand_wikidata"]
                branch = branch[len(key) :]
                break
        item["branch"] = re.sub(r"^tara jarmon\s+", "", branch.strip(), flags=re.IGNORECASE).title()

        # Only the displayed text is reliable; horaire_plus disagrees with it on most stores.
        hours = re.sub(r"<[^>]+>", " ", selector.xpath("@horaire").get(""))
        hours = re.sub(r"(\d)h(\d)", r"\1:\2", hours).replace(" and ", ", ")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours)

        apply_category(Categories.SHOP_CLOTHES, item)
        apply_category({"clothes": "women"}, item)
        yield item
