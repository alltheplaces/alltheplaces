import json
import re

import scrapy

from locations.items import Feature


class SignetJewelersSpider(scrapy.Spider):
    name = "signet_jewelers"
    allowed_domains = [
        "www.jared.com",
        "www.kay.com",
        "www.zales.com",
        "www.pagoda.com",
        "www.peoplesjewellers.com",
        "www.ernestjones.co.uk",
        "www.hsamuel.co.uk",
    ]
    download_delay = 0.5  # limit the delay to avoid 403 errors
    requires_proxy = True

    ca_prov = [
        "Alberta",
        "British Columbia",
        "Manitoba",
        "New Brunswick",
        "Newfoundland and Labrador",
        "Nova Scotia",
        "Ontario",
        "Saskatchewan",
    ]

    states = [
        "Alabama",
        "Alaska",
        "Arizona",
        "Arkansas",
        "California",
        "Colorado",
        "Connecticut",
        "Delaware",
        "Florida",
        "Georgia",
        "Hawaii",
        "Idaho",
        "Illinois",
        "Indiana",
        "Iowa",
        "Kansas",
        "Kentucky",
        "Louisiana",
        "Maine",
        "Maryland",
        "Massachusetts",
        "Michigan",
        "Minnesota",
        "Mississippi",
        "Missouri",
        "Montana",
        "Nebraska",
        "Nevada",
        "New Hampshire",
        "New Jersey",
        "New Mexico",
        "New York",
        "North Carolina",
        "North Dakota",
        "Ohio",
        "Oklahoma",
        "Oregon",
        "Pennsylvania",
        "Rhode Island",
        "South Carolina",
        "South Dakota",
        "Tennessee",
        "Texas",
        "Utah",
        "Vermont",
        "Virginia",
        "Washington",
        "West Virginia",
        "Wisconsin",
        "Wyoming",
    ]

    def start_requests(self):
        north_america_brands = ["jared", "kay", "zales", "pagoda", "peoplesjewellers"]

        uk_urls = [
            "https://www.hsamuel.co.uk/scripts/dist/store-locator/functionality/store-details.min.js?sprint-17_20190911.3",
            "https://www.ernestjones.co.uk/scripts/store-locator/storeLocationDetails.js",
        ]

        for url in uk_urls:
            yield scrapy.Request(url=url, callback=self.parse_uk)

        template = "https://www.{brand}.com/store-finder/view-stores/{region}"

        for brand in north_america_brands:
            if brand == "peoplesjewellers":
                for prov in SignetJewelersSpider.ca_prov:
                    url = template.format(brand=brand, region=prov)
                    yield scrapy.Request(url, callback=self.parse_cities)
            else:
                for state in SignetJewelersSpider.states:
                    url = template.format(brand=brand, region=state)
                    yield scrapy.Request(url, callback=self.parse_cities)

    def parse_cities(self, response):
        cities = response.xpath('//*[@class="viewstoreslist"]/a/@href').extract()
        for i in cities:
            yield scrapy.Request(response.urljoin(i), callback=self.parse)

    def parse(self, response):
        script = " ".join(response.xpath('//*[@id="js-store-details"]/div/script/text()').extract())
        data = None

        if re.search(r"storeInformation\s=\s((?s).*)", script) is not None:
            data = re.search(r"storeInformation\s=\s((?s).*)", script).groups()

        properties = {}

        if data is not None:
            if len(data) > 0:
                data = data[0]
            data = data.replace(";", "")
            data = eval(data)

            if data["region"] in SignetJewelersSpider.ca_prov:
                country = "CA"
            else:
                country = "US"

            properties = {
                "ref": data["name"],
                "name": data["displayName"],
                "addr_full": data["line1"],
                "city": data["town"],
                "state": data["region"],
                "postcode": data["postalCode"],
                "country": country,
                "lat": data["latitude"],
                "lon": data["longitude"],
                "phone": data["phone"],
                "website": response.url,
                "brand": re.search(r"www.(\w+)", response.url)[1],
            }

        yield Feature(**properties)

    def parse_uk(self, response):
        data = re.search(r"Signet.allStoreDetails=((?s).*)", response.text)[1]
        data = data.replace(";", "")
        data = json.loads(data)

        for store in data:
            properties = {
                "ref": store["number"],
                "name": store["name"],
                "addr_full": store["addressLine1"],
                "city": store["town"],
                "postcode": store["postcode"],
                "country": "GB",
                "lat": store["latitude"],
                "lon": store["longitude"],
                "brand": re.search(r"www.(\w+)", response.url)[1],
            }

            yield Feature(**properties)
