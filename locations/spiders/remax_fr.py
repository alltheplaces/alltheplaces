import json
import re

import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class RemaxFrSpider(scrapy.Spider):
    name = "remax_fr"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["remax.fr", "s.maxwork.fr"]

    def start_requests(self):
        url = "https://www.remax.fr/Api/Office/Search?size=2000"
        payload = json.dumps(
            {
                "filters": [
                    {"field": "OfficeName", "type": 0, "fuzziness": None},
                    {"field": "Region2ID", "type": 0},
                    {"field": "LanguagesSpokenIds", "type": 0},
                ]
            }
        )
        headers = {
            "content-type": "application/json",
            "languageid": "2",
            "user-agent": BROWSER_DEFAULT,
        }
        yield scrapy.Request(url=url, headers=headers, method="POST", body=payload, callback=self.parse)

    def parse(self, response):
        url = "https://s.maxwork.fr/site/static/2/offices/details_V2/{}.html"
        for data in response.json().get("results"):
            yield scrapy.Request(
                url=url.format(data.get("officeNumber")), callback=self.parse_agence, cb_kwargs={"properties": data}
            )

    def parse_agence(self, response, properties):
        street_address = (
            response.xpath('//p[contains(@class, "location-info-address hide-info-fr")]/text()[2]').get().strip()
        )
        postcode_city = response.xpath('//p[contains(@class, "location-info-address hide-info-fr")]/text()[3]').get()
        postcode = (re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", postcode_city)[0:1] or (None,))[0]
        city = postcode_city.replace(postcode, "").replace(",", "").replace(" ", "") if postcode else None
        lat, lon = (
            response.xpath('//a[@class="see-maps"]/@href')
            .get()
            .strip()
            .replace("https://www.google.com/maps/search/?api=1&query=", "")
            .split(",")
        )
        properties = {
            "ref": properties.get("officeNumber"),
            "name": properties.get("officeName"),
            "phone": properties.get("phoneNumber"),
            "street_address": street_address,
            "lat": lat,
            "lon": lon,
            "city": city,
            "postcode": postcode,
        }
        yield Feature(**properties)
