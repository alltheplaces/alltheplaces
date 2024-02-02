import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

BRANDS = {
    "banter": {"brand": "Banter by Piercing Pagoda", "brand_wikidata": "Q108410448"},
    "ernestjones": {"brand": "Ernest Jones", "brand_wikidata": "Q5393358"},
    "hsamuel": {"brand": "H.Samuel", "brand_wikidata": "Q5628558"},
    "jared": {"brand": "Jared", "brand_wikidata": "Q62029282"},
    "peoplesjewellers": {"brand": "Peoples Jewellers", "brand_wikidata": "Q64995558"},
    "zales": {"brand": "Zales", "brand_wikidata": "Q8065305"},
}


class SignetJewelersSpider(scrapy.Spider):
    name = "signet_jewelers"
    allowed_domains = [
        "www.jared.com",
        "www.zales.com",
        "www.banter.com",
        "www.peoplesjewellers.com",
        "www.ernestjones.co.uk",
        "www.hsamuel.co.uk",
    ]
    download_delay = 0.5  # limit the delay to avoid 403 errors

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
        # Pagoda has changed site to banter.com
        north_america_brands = ["banter", "jared", "peoplesjewellers", "zales"]

        uk_urls = [
            "https://www.hsamuel.co.uk/store-finder/view-stores/GB%20Region",
            "https://www.ernestjones.co.uk/store-finder/view-stores/GB%20Region",
        ]

        for url in uk_urls:
            yield scrapy.Request(url=url, callback=self.parse_cities)

        # Kay no longer use this store finder form, migrated to separate spider
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

        if re.search(r"(?s)storeInformation\s=\s(.*);", script) is not None:
            data = re.search(r"(?s)storeInformation\s=\s(.*);", script).group(1)
            data = json.loads(data.replace("y:", "y").replace("},", "}"))
            brand = re.search(r"www.(\w+)", response.url)[1]
            item = DictParser.parse(data)
            item["ref"] = data.get("name")
            item["name"] = data.get("displayName")
            item["website"] = response.url
            item["brand"] = BRANDS[brand]["brand"]
            item["brand_wikidata"] = BRANDS[brand]["brand_wikidata"]

            self.opening_hours(data.get("openings"), item)

            yield item

    def opening_hours(self, hours, item):
        if not hours:
            return

        oh = OpeningHours()
        for key, value in hours.items():
            oh.add_ranges_from_string("{day} {hours}".format(day=key, hours=value))
        item["opening_hours"] = oh
