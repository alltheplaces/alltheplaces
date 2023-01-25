from scrapy import Spider

from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature


class Brico_ioITSpider(Spider):
    name = "brico_io_it"
    item_attributes = {"brand_wikidata": "Q15965705"}
    start_urls = ["https://www.bricoio.it/api/organa/stores.aspx"]

    def parse(self, response, **kwargs):
        for location in response.json():
            if not location["Attivo"]:
                continue

            item = Feature()
            item["ref"] = location["Codice"]
            item["name"] = location["Nome"]
            item["street_address"] = location["Indirizzo"]["Descrizione"]
            item["city"] = location["Indirizzo"]["Localita"]
            item["state"] = location["Indirizzo"]["Provincia"]
            item["postcode"] = location["Indirizzo"]["CodicePostale"]
            item["country"] = location["Indirizzo"]["Nazione"]
            item["phone"] = location["Telefono"].replace("/", "")
            item["email"] = location["Email"]
            item["lat"] = location["Coordinate"]["Latitudine"]
            item["lon"] = location["Coordinate"]["Longitudine"]
            item["website"] = f'https://www.bricoio.it{location["URL"]}'

            item["opening_hours"] = OpeningHours()
            for rule in location["Orari"]["FasceOrarie"]:
                day = sanitise_day(rule["Giorno"][:3], DAYS_IT)
                for time in rule["Orario"].split(" / "):
                    start_time, end_time = time.split("-")
                    item["opening_hours"].add_range(day, start_time, end_time, time_format="%H.%M")

            yield item
