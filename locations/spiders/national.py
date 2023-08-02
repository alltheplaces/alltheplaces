import scrapy

from locations.items import Feature

HEADERS = {
    "authority": "prd.location.enterprise.com",
    "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
    "accept": "application/json, text/plain, */*",
    "sec-ch-ua-mobile": "?0",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "origin": "https://www.nationalcar.com",
    "referer": "https://www.nationalcar.com/",
    "accept-language": "en-US,en;q=0.9",
}


class NationalSpider(scrapy.Spider):
    name = "national"
    item_attributes = {"brand": "National Car Rental", "brand_wikidata": "Q1424142"}
    allowed_domains = ["nationalcar.com"]
    start_urls = ["https://www.nationalcar.com/en/car-rental/locations.html"]

    def start_requests(self):
        yield scrapy.Request(
            "https://prd.location.enterprise.com/enterprise-sls/search/location/national/web/all?cor=US&dto=true",
            headers=HEADERS,
        )

    def parse(self, response):
        loc_data = response.json()

        for loc in loc_data:
            properties = {
                "name": loc["name"],
                "brand": loc["brand"],
                "phone": loc["phones"][0]["phone_number"],
                "street_address": ", ".join(loc["address"]["street_addresses"]),
                "city": loc["address"]["city"],
                "state": loc["address"]["country_subdivision_code"],
                "postcode": loc["address"]["postal"],
                "country": loc["address"]["country_code"],
                "lat": float(loc["gps"]["latitude"]),
                "lon": float(loc["gps"]["longitude"]),
                "ref": loc["id"],
            }

            yield Feature(**properties)
