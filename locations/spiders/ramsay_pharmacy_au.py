from scrapy import Spider
from scrapy.http import JsonRequest


class RamsayPharmacyAUSpider(Spider):
    name = "ramsay_pharmacy_au"
    item_attributes = {"brand": "Ramsay Pharmacy", "brand_wikidata": ""}
    allowed_domains = ["ramsayportalapi-prod.azurewebsites.net"]
    start_urls = ["https://ramsayportalapi-prod.azurewebsites.net/api/pharmacyclient/pharmacies"]

    def start_requests(self):
        data = {
            "Distance": 0,
            "Is24Hours": False,
            "IsClickCollect": False,
            "IsOpenNow": False,
            "IsOpenWeekend": False,
            "Latitude": 0,
            "Longitude": 0,
            "OrderBy": "",
            "PageIndex": 1,
            "PageSize": 1000,
            "PharmacyName": "ramsay",
            "Region": None,
            "Services": None,
            "TodayId": 0,
            "TodayTime": "00:00:00",
            "WeekDayId": None,
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data, headers={"Origin": "https://www.ramsaypharmacy.com.au"})

    def parse(self, response):
        print(response.text())
