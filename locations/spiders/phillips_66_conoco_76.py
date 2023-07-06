import scrapy

from locations.items import Feature

BRANDS = {"U76": "76", "P66": "Phillips 66", "CON": "Conoco"}

WIKIBRANDS = {"U76": "Q1658320", "P66": "Q1656230", "CON": "Q214763"}


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
            yield Feature(
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
                brand=BRANDS[station["Brand"]],
                brand_wikidata=WIKIBRANDS[station["Brand"]],
                opening_hours="24/7" if station["TFH"] else "",
                extras={
                    "amenity:fuel": True,
                    "fuel:e85": station["e85"],
                    "fuel:diesel": station["Diesel"],
                    "fuel:biodiesel": station["rd"],
                    "car_wash": station["CarWash"],
                    "shop": "convenience" if station["CStore"] else "kiosk" if station["Snacks"] else None,
                    "atm": station["ATM"],
                },
            )
