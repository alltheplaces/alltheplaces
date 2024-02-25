import scrapy
from scrapy import Selector

from locations.categories import Categories
from locations.items import Feature

countries = (
    "Algeria,DZ",
    "Argentina,AR",
    "Australia,AU",
    "Austria,AT",
    "Azerbaijan,AZ",
    "Belgium,BE",
    "Brazil,BR",
    "Canada,CA",
    "Chile,CL",
    "China,CN",
    "Colombia,CO",
    "Czech Republic,CZ",
    "Denmark,DK",
    "Dominican Republic,DO",
    "Ecuador,EC",
    "Egypt,EG",
    "Finland,FI",
    "France,FR",
    "Germany,DE",
    "Greece,GR",
    "Hungary,HU",
    "India,IN",
    "Indonesia,ID",
    "Ireland,IE",
    "Israel,IL",
    "Italy,IT",
    "Kazakhstan,KZ",
    "Korea,KR",
    "Latvia,LV",
    "Malaysia,MY",
    "Mexico,MX",
    "Morocco,MA",
    "Myanmar,MM",
    "Netherlands,NL",
    "Norway,NO",
    "Panama,PA",
    "Peru,PE",
    "Philippines,PH",
    "Poland,PL",
    "Portugal,PT",
    "Qatar,QA",
    "Romania,RO",
    "Russia,RU",
    "Saudi Arabia,SA",
    "Singapore,SG",
    "South Africa,ZA",
    "Spain,ES",
    "Sweden,SE",
    "Switzerland,CH",
    "Taiwan,TW",
    "Thailand,TH",
    "Tunisia,TN",
    "Turkey,TR",
    "Ukraine,UA",
    "United Arab Emirates,AE",
    "United Kingdom,UK",
    "United States,US",
    "Uzbekistan,UZ",
    "Venezuela,VE",
    "Vietnam,VN",
)


class AlstomSpider(scrapy.Spider):
    # download_delay = 0.3
    name = "alstom"
    item_attributes = {"brand": "Alstom", "brand_wikidata": "Q309084", "extras": Categories.OFFICE_COMPANY.value}
    allowed_domains = ["alstom.com"]
    start_urls = ("https://www.alstom.com/alstom-page/maps/json/1826",)

    def parse(self, response):
        for i in response.json():
            for j in i["locations"]:
                try:
                    lng = float(j["long"])
                except:
                    lng = j["long"].replace(",", "").replace(".", "")
                    lng = lng[:3] + "." + lng[3:]
                try:
                    lat = float(j["lat"].strip("\u200b"))
                except:
                    lat = j["lat"].replace(",", "").replace(".", "")
                    lat = lat[:3] + "." + lat[3:]
                if not j["address"]:
                    j["address"] = ""
                addr = Selector(text=j["address"]).xpath("//p/text()").get()

                properties = {
                    "ref": j["id"],
                    "name": j["title"],
                    "addr_full": addr,
                    "country": i["name"],
                    "phone": j["phone"] or None,
                    "lat": float(lat),
                    "lon": float(lng),
                }

                yield Feature(**properties)
