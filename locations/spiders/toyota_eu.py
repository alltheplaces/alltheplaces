import pycountry
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

    all_countries = [country.alpha_2.lower() for country in pycountry.countries]
    exclude_countries = [
        "bf",  # toyota_africa
        "bj",
        "cd",
        "cf",
        "cg",
        "ci",
        "cm",
        "gm",
        "gn",
        "gq",
        "gw",
        "ke",
        "lr",
        "mg",
        "ml",
        "mr",
        "mz",
        "ne",
        "ng",
        "rw",
        "sl",
        "sn",
        "td",
        "tg",
        "ug",
        "zw",
        "au",  # toyota_au
        "br",  # toyota_br
        "nz",  # toyota_nz
        "bw",  # toyota_sacu
        "ls",
        "na",
        "sz",
        "za",
        "us",  # toyota_us
    ]

    def start_requests(self):
        available_countries = [c for c in self.all_countries if c not in self.exclude_countries]
        for country in available_countries:
            yield scrapy.Request(
                f"https://kong-proxy-intranet.toyota-europe.com/dxp/dealers/api/toyota/{country}/en/all",
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
