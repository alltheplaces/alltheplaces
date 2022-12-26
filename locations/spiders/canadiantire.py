import re

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from locations.user_agents import BROSWER_DEFAULT


class CanadianTireSpider(scrapy.spiders.SitemapSpider):
    name = "canadiantire"
    item_attributes = {"brand": "Canadian Tire", "brand_wikidata": "Q1032400"}
    allowed_domains = ["canadiantire.ca"]
    sitemap_urls = [
        "https://www.canadiantire.ca/sitemap_store_en_01.xml",
    ]
    sitemap_rules = [("", "parse_store")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.canadiantire.ca",
            "User-Agent": BROSWER_DEFAULT,
        },
    }

    def parse_store(self, response):
        headers = {
            "User-Agent": BROSWER_DEFAULT,
            "Host": "apim.canadiantire.ca",
            "baseSiteId": "CTR",
            "Ocp-Apim-Subscription-Key": "c01ef3612328420c9f5cd9277e815a0e",
        }
        id_url = re.findall("[0-9]+", response.url)[0]
        template = "https://apim.canadiantire.ca/v1/store/store/{id_url}?lang=en_CA"

        yield scrapy.Request(url=template.format(id_url=id_url), headers=headers, callback=self.parse_store_details)

    def parse_store_details(self, response):

        oh = OpeningHours()
        if response.json().get("storeServices"):
            for day in response.json().get("storeServices", {})[0].get("weekDayOpeningList"):
                if day.get("closed"):
                    continue
                oh.add_range(
                    day=day.get("weekDay"),
                    open_time=day.get("openingTime", {}).get("formattedHour").replace(".", ""),
                    close_time=day.get("closingTime", {}).get("formattedHour").replace(".", ""),
                    time_format="%I:%M %p",
                )

        properties = {
            "ref": response.json().get("id"),
            "name": response.json().get("name"),
            "postcode": response.json().get("address", {}).get("postalCode"),
            "country": response.json().get("address", {}).get("country", {}).get("isocode"),
            "lat": response.json().get("geoPoint", {}).get("latitude"),
            "lon": response.json().get("geoPoint", {}).get("longitude"),
            "phone": response.json().get("address", {}).get("phone"),
            "email": response.json().get("address", {}).get("email"),
            "street_address": response.json().get("address", {}).get("line1"),
            "website": f'https://www.canadiantire.ca{response.json().get("url")}',
            "opening_hours": oh.as_opening_hours(),
        }

        yield GeojsonPointItem(**properties)
