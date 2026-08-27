import re

from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature


class LeComptoirIrlandaisFRSpider(Spider):
    name = "le_comptoir_irlandais_fr"
    item_attributes = {"brand": "Le Comptoir Irlandais", "brand_wikidata": "Q3221668"}

    allowed_domains = ["comptoir-irlandais.com"]

    start_urls = [
        "https://www.comptoir-irlandais.com/fr/storefinder?ajax=1&all=1",
    ]

    def parse(self, response):
        stores = response.xpath("//markers//marker")

        for store in stores:
            item = Feature(**self.item_attributes)
            apply_category(Categories.SHOP_DELI, item)

            item["ref"] = store.attrib.get("id_store")
            item["branch"] = (
                store.attrib.get("name")
                .removeprefix("Le Comptoir Irlandais ")
                .removeprefix("de ")
                .removeprefix("du ")
                .removeprefix("d'")
            )
            item["addr_full"] = " ".join(store.attrib.get("address").split("<br />")[:2])

            item["lat"] = store.attrib.get("lat")
            item["lon"] = store.attrib.get("lng")

            match = re.search(r"\b\d{5}\b", store.attrib.get("address"))
            item["postcode"] = match.group() if match else None
            item["country"] = "France"

            item["phone"] = store.attrib.get("phone")
            item["website"] = store.attrib.get("link")

            selector = Selector(text=store.attrib.get("other"))

            item["opening_hours"] = OpeningHours()
            for row in selector.xpath("//table//tbody/tr"):
                day = row.xpath("string(./td[1])").get().strip()
                hours = row.xpath("string(./td[2])").get().strip()
                item["opening_hours"].add_ranges_from_string(
                    day + " " + hours.replace("h30", ":30").replace("h", ":00"),
                    DAYS_FR,
                    delimiters=DELIMITERS_FR,
                    closed=CLOSED_FR,
                )
            yield item
