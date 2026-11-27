from typing import Iterable
from urllib.parse import urlparse

from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LaserGameEvolutionSpider(StructuredDataSpider):
    name = "laser_game_evolution"
    item_attributes = {
        "brand": "Laser Game Evolution",
        "brand_wikidata": "Q130214296",
    }
    start_urls = ["https://lasergame-evolution.com/toutes-les-salles/"]
    wanted_types = ["EntertainmentBusiness"]
    name_is_branch = True
    drop_attributes = {"image"}

    def parse(self, response: Response, **kwargs):
        for centre in response.css("a.lct-salles-item"):
            callback = self.parse_canada if "lasergame-evolution.ca" in centre.attrib["href"] else self.parse_sd
            yield response.follow(centre, callback=callback)

    def parse_canada(self, response: TextResponse, **kwargs):
        # The .ca pages only publish BreadcrumbList JSON-LD, they have to be handled differently by parsing their HTML instead.
        item = Feature()
        item["ref"] = response.url
        item["branch"] = response.css("h1::text").get()
        item["website"] = response.url
        item["addr_full"] = response.css('#coordonnees a[href*="goo.gl"] p::text').get()
        item["phone"] = response.css('#coordonnees a[href^="tel:"]::text').get()
        item["country"] = "CA"
        extract_google_position(item, response)
        apply_category(Categories.AMUSEMENT_ARCADE_LASER_TAG, item)
        yield item

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item["branch"].removeprefix("Laser Game Evolution ").strip()
        # Every country site hardcodes addressCountry=FR, so use the TLD instead.
        country = urlparse(response.url).hostname[-2:].upper()
        item["country"] = {"La Réunion": "RE", "Nouvelle-Calédonie": "NC"}.get(item["state"], country)
        if item["country"] == "CH":
            item["city"] = item["branch"]  # Source locality also contains canton and country.
        item["state"] = None
        apply_category(Categories.AMUSEMENT_ARCADE_LASER_TAG, item)
        yield item
