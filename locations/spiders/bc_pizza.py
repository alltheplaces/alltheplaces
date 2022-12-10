import re
import scrapy
from datetime import datetime
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from locations.google_url import extract_google_position

# source: https://gist.github.com/rogerallen/1583593
us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}


class BcpizzaSpider(scrapy.Spider):
    name = "bcpizza"
    item_attributes = {"brand": "BC Pizza"}
    allowed_domains = ["bc.pizza"]
    start_urls = ["https://bc.pizza/project-cat/bc-pizza-locations/"]

    def parse(self, response):
        urls = response.xpath("//a[@rel='bookmark']/@href").extract()
        for url in urls:
            yield scrapy.Request(url, self.parse_locations)

    def parse_locations(self, response):
        name = response.xpath('//div[@class="wpb_wrapper"]/h1/text()').get()
        address_full = response.xpath(
            '//div[@class="wpb_text_column wpb_content_element"]//p/text()'
        ).get()
        address = response.xpath(
            'string(//div[@class="wpb_text_column wpb_content_element"]//p)'
        ).get()
        if address == address_full:
            address = response.xpath(
                '//div[@class="wpb_text_column wpb_content_element"]//p[2]/text()'
            ).get()
        city_state_postcode = address.replace(address_full, "").replace("\n", "")
        postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", city_state_postcode)[
            0
        ]
        city = city_state_postcode.split(",")[0]
        state = city_state_postcode.split(",")[1].replace(postcode, "").strip()
        if state in us_state_to_abbrev:
            state = us_state_to_abbrev[state]
        phone = response.xpath('//a[contains(@href, "tel")]/text()').get()
        facebook = response.xpath('//a[@class="vc_icon_element-link"]/@href').get()
        days = response.xpath('//table[contains(@class, "op-table")]//tr')
        oh = OpeningHours()

        for i, day in enumerate(days):
            dd = day.xpath(f"//tr[{i+1}]//th/text()").get()
            hh = day.xpath(f"//tr[{i+1}]//span/text()").get()
            if hh == "Closed":
                continue
            open_time, close_time = hh.split(" – ")
            oh.add_range(
                day=dd,
                open_time=datetime.strftime(
                    datetime.strptime(open_time, "%I:%M %p"), "%H:%M"
                ),
                close_time=datetime.strftime(
                    datetime.strptime(close_time, "%I:%M %p"), "%H:%M"
                ),
            )

        properties = {
            "ref": response.url,
            "name": name,
            "city": city,
            "state": state,
            "postcode": postcode,
            "addr_full": address_full,
            "phone": phone,
            "facebook": facebook,
            "opening_hours": oh.as_opening_hours(),
        }

        extract_google_position(properties, response)

        yield GeojsonPointItem(**properties)
