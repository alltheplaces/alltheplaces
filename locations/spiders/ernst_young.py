import scrapy

from locations.items import Feature


class ErnstYoungSpider(scrapy.Spider):
    name = "ernst_young"
    item_attributes = {"brand": "EY", "brand_wikidata": "Q489097"}
    allowed_domains = []
    start_urls = [
        "https://www.ey.com/eydff/services/officeLocations.json",
    ]

    def parse_office(self, office):
        properties = {
            "name": office["name"],
            "ref": office["href"].replace("/locations/", ""),
            "city": office["officeCity"],
            "postcode": office["officePostalCode"],
            "country": office["officeCountry"],
            "phone": office["officePhoneNumber"],
            "lat": float(office["officeLatitude"]),
            "lon": float(office["officeLongitude"]),
        }
        if office["officeAddress"]:
            properties["street_address"] = office["officeAddress"].strip().replace("\r\n", " ")
        return properties

    def parse(self, response):
        data = response.json()

        for country in data["countries"]:
            for state in country["states"]:
                state_abbr = state["stateAbbreviation"]
                for city in state["cities"]:
                    for office in city["offices"]:
                        properties = self.parse_office(office)
                        properties["state"] = state_abbr
                        properties["website"] = response.urljoin(office["href"])
                        yield Feature(**properties)

            for city in country["cities"]:
                for office in city["offices"]:
                    properties = self.parse_office(office)
                    properties["website"] = response.urljoin(office["href"])
                    yield Feature(**properties)
