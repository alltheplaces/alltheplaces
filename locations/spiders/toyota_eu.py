import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaEUSpider(JSONBlobSpider):
    name = "toyota_eu"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    locations_key = "dealers"
    available_countries = {
        "am": "",
        "at": "",
        "az": "",
        "ba": "",
        "be": "",
        "bg": "",
        "ch": "",
        "cy": "",
        "cz": "",
        "de": "",
        "dk": "",
        "ee": "",
        "es": "",
        "fi": "",
        "fr": "MC",
        "gb": "je|im|gg",
        "ge": "",
        "gr": "",
        "hr": "",
        "hu": "",
        "is": "",
        "it": "",
        "lt": "",
        "lv": "",
        "nl": "",
        "no": "",
        "pl": "",
        "pt": "",
        "ro": "",
        "rs": "",
        "ru": "",
        "se": "",
        "si": "",
        "sk": "",
        "tr": "",
        "ua": "",
    }

    def start_requests(self):
        for country, extra_countries in self.available_countries.items():
            yield scrapy.Request(
                f"https://kong-proxy-intranet.toyota-europe.com/dxp/dealers/api/toyota/{country}/en/all?extraCountries={extra_countries}",
                callback=self.parse,
            )

    def pre_process_data(self, feature):
        feature["geo"] = feature["address"].pop("geo", None)
        feature["email"] = feature.pop("eMail")

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_CAR, item)
        item["country"] = location["country"]
        item["street_address"] = clean_address(
            [location["address"].get("address1"), location["address"].get("address")]
        )
        set_social_media(item, SocialMedia.WHATSAPP, location.get("whatsapp"))

        oh = OpeningHours()
        for day in location["openingDays"]:
            if day["originalService"] == "ShowRoom":
                for hours in day["hours"]:
                    oh.add_ranges_from_string(
                        f"{day['startDayCode']}-{day['endDayCode']} {hours['startTime']}-{hours['endTime']}"
                    )
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_hours_type/{day['originalService']}")
        item["opening_hours"] = oh
        yield item
