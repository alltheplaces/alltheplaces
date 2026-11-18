import json
import re
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature


class BanqueMichelInchauspeFRSpider(Spider):
    name = "banque_michel_inchauspe_fr"
    item_attributes = {
        "brand": "Banque Michel Inchauspé",
        "brand_wikidata": "Q99647022",
        "name": "Banque Michel Inchauspé",
    }
    # The sitemap lists a pre-production host and dead agency URLs; the agency list is accurate.
    start_urls = ["https://www.banquebami.fr/contact_agence"]
    custom_settings = {"DOWNLOAD_DELAY": 10}  # robots.txt Crawl-delay

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.css(".bami-agency-location-more::attr(data-href)").getall():
            yield response.follow(url, callback=self.parse_agency)

    def parse_agency(self, response: Response) -> Any:
        item = Feature()
        item["ref"] = response.css('link[rel="shortlink"]::attr(href)').re_first(r"/node/(\d+)") or response.url
        item["website"] = response.url
        item["branch"] = response.css(".bami-agency-location-name::text").get("").strip()
        item["phone"] = response.css(".bami-agency-location-phone::text").get()
        item["email"] = response.css(".bami-agency-location-email a::text").get()
        if fax := response.css(".bami-agency-location-fax::text").get():
            item["extras"]["fax"] = fax

        # Coordinates and the split address are only published in the embedded map settings.
        settings = json.loads(
            response.xpath('//script[contains(text(), "Drupal.settings")]/text()').re_first(
                r"Drupal\.settings, (\{.+\})\);", default="{}"
            )
        )
        for gmap in settings.get("gmap", {}).values():
            for marker in gmap.get("markers", []):
                item["lat"], item["lon"] = marker["latitude"], marker["longitude"]
                address = Selector(text=marker["text"])
                item["street_address"] = address.css('[itemprop="streetAddress"]::text').get()
                item["postcode"] = address.css('[itemprop="postalCode"]::text').get()
                item["city"] = address.css('[itemprop="addressLocality"]::text').get("").strip()

        item["opening_hours"] = OpeningHours()
        for hours in response.css(".bami-agency-time .row-time .field-content::text").getall():
            item["opening_hours"].add_ranges_from_string(
                re.sub(r"(\d)h(\d)", r"\1:\2", hours), days=DAYS_FR, delimiters=DELIMITERS_FR
            )

        apply_category(Categories.BANK, item)
        yield item
