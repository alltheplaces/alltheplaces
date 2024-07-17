import scrapy

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class McDonaldsSpider(scrapy.Spider):
    name = "mcdonalds"
    item_attributes = {
        "brand": "McDonald's",
        "brand_wikidata": "Q38076",
        "extras": Categories.FAST_FOOD.value,
    }
    allowed_domains = ["www.mcdonalds.com"]

    def start_requests(self):
        template = "https://www.mcdonalds.com/googleappsv2/geolocation?latitude={}&longitude={}&radius=50&maxResults=250&country={}&language={}&showClosed="
        for locale in [
            "en-ca",
            "en-gb",
            "fi-fi",
            "en-ie",
            "en-us",
            "de-de",
            "nb-no",
            "en-ae",
            "dk-dk",
            "nl-nl",
            "en-om",
            "en-qa",
            "en-kw",
            "en-bh",
            "fr-ch",
            "sv-se",
            "en-sa",
            "uk-ua",
            "hu-hu",
            "zh-tw",
        ]:
            country = locale.split("-")[1]
            for city in city_locations(country.upper(), 20000):
                if country == "sa":
                    url = template.format(city["latitude"], city["longitude"], "sar", "en")
                else:
                    url = template.format(city["latitude"], city["longitude"], country, locale)
                yield scrapy.Request(
                    url,
                    self.parse_major_api,
                    cb_kwargs=dict(country=country, locale=locale),
                )

    def parse_major_api(self, response, country, locale):
        if len(response.body) == 0:
            return
        stores = response.json()["features"]
        for store in stores:
            properties = store["properties"]
            store_identifier = properties["identifierValue"]
            store_url = None
            if locale in [
                "en-ca",
                "en-gb",
                "en-ie",
                "en-us",
                "fi-fi",
                "fr-ch",
                "hu-hu",
                "sv-se",
                "zh-tw",
            ]:
                # Individual store site pages in these locale's have a common pattern.
                store_url = "https://www.mcdonalds.com/{}/{}/location/{}.html".format(country, locale, store_identifier)
            elif locale in ["de-de"]:
                store_url = properties.get("restaurantUrl")
                if not store_url.startswith("https://www.mcdonalds.com/"):
                    # Most of the sites have good individual site pages, some do not.
                    store_url = None
            elif locale in [
                "nb-no",
                "en-ae",
                "en-om",
                "en-qa",
                "en-kw",
                "en-bh",
                "en-sa",
            ]:
                # These locale's do not support individual site pages.
                pass
            elif locale in ["da-dk", "nl-nl"]:
                store_url = properties.get("restaurantUrl")
            if not store_url:
                store_url = "https://www.mcdonalds.com/"

            item = DictParser.parse(properties)
            item["ref"] = store_identifier
            item["website"] = store_url
            item["street_address"] = clean_address([properties.get("addressLine1"), properties.get("addressLine2")])
            item["city"] = properties.get("addressLine3")
            item["state"] = properties.get("subDivision")
            item["country"] = country.upper()
            item["lon"], item["lat"] = store["geometry"]["coordinates"]

            # hu-hu has non-standard filterType values
            filter_type = [p.replace("restaurant.facility.", "").upper() for p in properties["filterType"]]

            apply_yes_no(Extras.DRIVE_THROUGH, item, "DRIVETHRU" in filter_type)
            apply_yes_no(Extras.WIFI, item, "WIFI" in filter_type)
            apply_yes_no(Extras.DELIVERY, item, "MCDELIVERYSERVICE" in filter_type)

            if hours := self.store_hours(properties.get("restauranthours")):
                item["opening_hours"] = hours

            yield item

    def store_hours(self, store_hours):
        if not store_hours:
            return None

        oh = OpeningHours()
        for day in DAYS_FULL:
            if hours := store_hours.get("hours" + day):
                try:
                    start_time, end_time = hours.split(" - ")
                    oh.add_range(day, start_time.replace("24:00", "00:00"), end_time)
                except:
                    self.logger.debug(f"Couldn't process opening hours: {hours}")
        return oh
