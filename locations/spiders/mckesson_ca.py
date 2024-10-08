from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FR, OpeningHours


class MckessonCASpider(Spider):
    name = "mckesson_ca"
    allowed_domains = [
        "www.guardian-ida-remedysrx.ca",
        "www.uniprix.com",
    ]
    start_urls = [
        "https://www.guardian-ida-remedysrx.ca/api/sitecore/Pharmacy/Pharmacies?id=%7B73B789E3-C922-483E-9E5A-C1D2BC52D6D4%7D",
        "https://www.uniprix.com/api/sitecore/Pharmacy/Pharmacies?id=%7B1D46A582-AF24-4EC2-87BA-AFFC76B73967%7D",
    ]
    brands = {
        "G": {"brand": "Guardian", "brand_wikidata": "Q65553864"},
        "I": {"brand": "I.D.A.", "brand_wikidata": "Q65553883"},
        "R": {"brand": "Remedy'sRx", "brand_wikidata": "Q65553833"},
        "UM": {"brand": "Uniprix", "brand_wikidata": "Q683265"},
        "UQ": {"brand": "Uniprix", "brand_wikidata": "Q683265"},
        "UX": {"brand": "Uniprix", "brand_wikidata": "Q683265"},
    }

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["pharmacies"]:
            item = DictParser.parse(location)
            item.update(self.brands[location["banner"]])
            if location["banner"] in ["G", "I", "R"]:
                item["website"] = "https://www.guardian-ida-remedysrx.ca" + location["detailUrl"]
            if location["banner"] in ["UM", "UQ", "UX"]:
                item["website"] = "https://www.uniprix.com" + location["detailUrl"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["storeOpeningHours"]:
                if day_hours["isClose"] or day_hours["isNotAvailable"]:
                    continue
                if day_hours["displayLanguage"]["Name"] == "en":
                    item["opening_hours"].add_range(
                        DAYS_EN[day_hours["day"]], day_hours["startTime"], day_hours["endTime"], "%H:%M:%S"
                    )
                elif day_hours["displayLanguage"]["Name"] == "fr":
                    item["opening_hours"].add_range(
                        DAYS_FR[day_hours["day"]], day_hours["startTime"], day_hours["endTime"], "%H:%M:%S"
                    )
            yield item
