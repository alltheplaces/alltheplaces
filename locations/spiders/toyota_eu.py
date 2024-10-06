import pycountry
import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaEUSpider(JSONBlobSpider):
    download_timeout = 60
    name = "toyota_eu"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    locations_key = "dealers"

    all_countries = [country.alpha_2.lower() for country in pycountry.countries]
    exclude_countries = [
        "au",  # toyota_au
        "bf",  # toyota_africa
        "bj",  # toyota_africa
        "br",  # toyota_br
        "bw",  # toyota_sacu
        "cd",  # toyota_africa
        "cf",  # toyota_africa
        "cg",  # toyota_africa
        "ci",  # toyota_africa
        "cm",  # toyota_africa
        "gm",  # toyota_africa
        "gn",  # toyota_africa
        "gq",  # toyota_africa
        "gw",  # toyota_africa
        "ke",  # toyota_africa
        "lr",  # toyota_africa
        "ls",  # toyota_sacu
        "mg",  # toyota_africa
        "ml",  # toyota_africa
        "mr",  # toyota_africa
        "mz",  # toyota_africa
        "na",  # toyota_sacu
        "ne",  # toyota_africa
        "ng",  # toyota_africa
        "nz",  # toyota_nz
        "rw",  # toyota_africa
        "sl",  # toyota_africa
        "sn",  # toyota_africa
        "sz",  # toyota_sacu
        "td",  # toyota_africa
        "tg",  # toyota_africa
        "tw",  # toyota_tw
        "ug",  # toyota_africa
        "us",  # toyota_us
        "za",  # toyota_sacu
        "zw",  # toyota_africa
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
        services = [i["service"] for i in location["services"]]
        for service in services:
            self.crawler.stats.inc_value(f"atp/{self.name}/services/{service}")
        if "ShowRoom" in services:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, "WorkShop" in services, False)
            apply_yes_no(Extras.USED_CAR_SALES, item, "UsedCars" in services, False)
            apply_yes_no(Extras.CAR_PARTS, item, "PartsShop" in services)
        elif "UsedCars" in services:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.USED_CAR_SALES, item, True)
            apply_yes_no(Extras.NEW_CAR_SALES, item, False, False)
            apply_yes_no(Extras.CAR_REPAIR, item, "WorkShop" in services, False)
        elif "WorkShop" in services:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        elif "PartsShop" in services:
            apply_category(Categories.SHOP_CAR_PARTS, item)
        else:  # Some locations have no services listed, so fall back to shop=car
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
