import re

import scrapy
from scrapy.selector import Selector

from locations.geo import postal_regions
from locations.items import Feature


class VetcoClinicsSpider(scrapy.Spider):
    name = "vetco"
    item_attributes = {"brand": "Vetco Clinics"}
    allowed_domains = ["vetcoclinics.com"]

    def start_requests(self):
        for record in postal_regions("US"):
            url_template = "https://www.vetcoclinics.com/_assets/dynamic/ajax/locator.php?zip={}"
            yield scrapy.http.Request(url_template.format(record["postal_region"]))

    def parse(self, response):
        jsonresponse = response.json()
        if jsonresponse is not None:
            clinics = jsonresponse.get("clinics")
            if clinics:
                for stores in clinics:
                    body = stores["label"]
                    address = Selector(text=body).xpath("//address/text()").extract()
                    if len(address) == 3:
                        addr_full, city_state_postal, phone = (item.split(",") for item in address)
                        city, state_postal = (item.split(",") for item in city_state_postal)
                        state, postal = re.search(r"([A-Z]{2}) (\d{5})", state_postal[0]).groups()

                    else:
                        addr_full, city_state_postal = (item.split(",") for item in address)
                        city, state_postal = (item.split(",") for item in city_state_postal)
                        state, postal = re.search(r"([A-Z]{2}) (\d{5})", state_postal[0]).groups()

                    properties = {
                        "ref": addr_full[0].strip(),
                        "addr_full": addr_full[0].strip(),
                        "city": city[0].strip(),
                        "state": state,
                        "postcode": postal,
                        "lat": float(stores["point"]["lat"]),
                        "lon": float(stores["point"]["long"]),
                        "website": response.url,
                    }

                    yield Feature(**properties)
