# -*- coding: utf-8 -*-
import scrapy

from locations.geo import city_locations
from locations.dict_parser import DictParser


class McDonaldsSpider(scrapy.Spider):
    name = "mcdonalds"
    item_attributes = {"brand": "McDonald’s", "brand_wikidata": "Q38076"}
    allowed_domains = ["www.mcdonalds.com"]
    download_delay = 0.5

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
        ]:
            country = locale.split("-")[1]
            for city in city_locations(country.upper(), 20000):
                if country == "sa":
                    url = template.format(
                        city["latitude"], city["longitude"], "sar", "en"
                    )
                else:
                    url = template.format(
                        city["latitude"], city["longitude"], country, locale
                    )
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
                "fi-fi",
                "en-ie",
                "en-us",
                "fr-ch",
                "sv-se",
                "zh-tw",
            ]:
                # Individual store site pages in these locale's have a common pattern.
                store_url = "https://www.mcdonalds.com/{}/{}/location/{}.html".format(
                    country, locale, store_identifier
                )
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
            item["street_address"] = properties.get("addressLine1")
            item["city"] = properties.get("addressLine3")
            item["state"] = properties.get("subDivision")
            item["country"] = country.upper()
            coords = store["geometry"]["coordinates"]
            item["lat"] = coords[1]
            item["lon"] = coords[0]

            hours = properties.get("restauranthours")
            try:
                hours = self.store_hours(hours)
                if hours:
                    item["opening_hours"] = hours
            except:
                self.logger.exception("Couldn't process opening hours: %s", hours)

            yield item

    def store_hours(self, store_hours):
        if not store_hours:
            return None
        if all([h == "" for h in store_hours.values()]):
            return None

        day_groups = []
        this_day_group = None
        for day in (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ):
            hours = store_hours.get("hours" + day)
            if not hours:
                continue

            hours = hours.replace(" - ", "-")
            day_short = day[:2]

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day_short
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
        day_groups.append(this_day_group)

        if len(day_groups) == 1:
            opening_hours = day_groups[0]["hours"]
            if opening_hours == "04:00-04:00":
                opening_hours = "24/7"
        else:
            opening_hours = ""
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours
