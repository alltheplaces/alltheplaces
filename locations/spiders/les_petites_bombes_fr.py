from scrapy import Spider

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature


class LesPetitesBombesFRSpider(Spider):
    name = "les_petites_bombes_fr"
    item_attributes = {"brand": "Les Petites Bombes", "brand_wikidata": "Q141190957"}

    allowed_domains = ["lespetitesbombes.com"]

    start_urls = [
        "https://lespetitesbombes.com/pages/store-locator-les-petites-bombes",
    ]

    def parse(self, response):
        stores = response.css("map-viewer template")

        for store in stores:
            item = Feature()
            apply_category(Categories.SHOP_CLOTHES, item)
            apply_clothes(Clothes.WOMEN, item)

            item["ref"] = store.attrib.get("name")

            branch = store.css(".map-place-list__modal-store-name::text").get()
            item["branch"] = branch.removeprefix("LPB ") if branch else None

            item["addr_full"] = store.css(".map-place-list__modal-address::text").get()
            item["lat"] = store.attrib.get("latitude")
            item["lon"] = store.attrib.get("longitude")

            city = store.css(".map-place-list__modal-city::text").get()
            if city:
                parts = city.split("\xa0")
                if len(parts) == 2:
                    item["postcode"], item["city"] = parts

            item["country"] = store.css(".map-place-list__modal-country::text").get()

            item["phone"] = store.css('a[href^="callto:"]::text').get()
            item["email"] = store.css('a[href^="mailto:"]::text').get()

            permanently_closed = False
            item["opening_hours"] = OpeningHours()
            for day in store.css(".map-place-list__modal-store-opening-hours::text").getall():
                if "définitivement" in day:  # the shop is permanently closed
                    permanently_closed = True

                item["opening_hours"].add_ranges_from_string(day, DAYS_FR, delimiters=DELIMITERS_FR ,closed=CLOSED_FR)
                print(day)

            if not permanently_closed:
                yield item
