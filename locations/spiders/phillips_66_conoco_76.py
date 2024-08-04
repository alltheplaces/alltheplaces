import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class Phillips66Conoco76Spider(scrapy.Spider):
    name = "phillips_66_conoco_76"
    allowed_domains = ["spatial.virtualearth.net"]
    base_url = (
        "https://spatial.virtualearth.net/REST/v1/data/a1ed23772f5f4994a096eaa782d07cfb/US_BrandedSites/Sites"
        "?key=AvroZVNGVuRnilfbaoMSyXJhjA36NTNr8jdIufcn1erJ_kJMF5UE33M_ENXxHwTb"
        "&$filter=(Brand eq 'P66' OR Brand ne 'P66')"
        "&$select=EntityID,Latitude,Longitude,Name,AddressLine,Locality,AdminDistrict,PostalCode,CountryRegion,Phone,"
        "Brand,TFH,e85,Diesel,rd,CarWash,CStore,Snacks,ATM"
    )

    BRANDS = {
        "76": {"brand": "U76", "brand_wikidata": "Q1658320"},
        "U76": {"brand": "U76", "brand_wikidata": "Q1658320"},
        "CON": {"brand": "Conoco", "brand_wikidata": "Q1126518"},
        "COP": None,
        "P66": {"brand": "Phillips 66", "brand_wikidata": "Q1656230"},
    }

    def start_requests(self):
        yield scrapy.Request(
            self.base_url + "&$inlinecount=allpages" + "&$format=json",
            callback=self.get_pages,
        )

    def get_pages(self, response):
        total_count = int(response.json()["d"]["__count"])
        offset = 0
        page_size = 250

        while offset < total_count:
            yield scrapy.Request(self.base_url + f"&$top={page_size}&$skip={offset}&$format=json")
            offset += page_size

    def parse(self, response):
        stations = response.json()["d"]["results"]

        for station in stations:
            item = Feature(
                lat=station["Latitude"],
                lon=station["Longitude"],
                name=station["Name"],
                street_address=station["AddressLine"],
                city=station["Locality"],
                state=station["AdminDistrict"],
                postcode=station["PostalCode"],
                country=station["CountryRegion"],
                phone=station["Phone"],
                ref=station["EntityID"],
                opening_hours="24/7" if station["TFH"] else "",
            )
            if brand := self.BRANDS.get(station["Brand"]):
                item.update(brand)

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.E85, item, station["e85"])
            apply_yes_no(Fuel.DIESEL, item, station["Diesel"])
            apply_yes_no(Fuel.BIODIESEL, item, station["rd"])
            apply_yes_no(Extras.ATM, item, station["ATM"])
            apply_yes_no("shop=yes", item, station["CStore"] or station["Snacks"])

            yield item
