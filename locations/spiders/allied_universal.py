import scrapy

from locations.items import GeojsonPointItem

USA_STATES = {
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AS": "American Samoa",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DC": "District of Columbia",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "PR": "Puerto Rico",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VI": "Virgin Islands",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}

MEXICO_STATES = {
    "AG": "Aguascalientes",
    "BC": "Baja California Norte",
    "BS": "Baja California Sur",
    "CH": "Chihuahua",
    "CL": "Colima",
    "CM": "Campeche",
    "CO": "Coahuila",
    "CS": "Chiapas",
    "DF": "Distrito Federal",
    "DG": "Durango",
    "GR": "Guerrero",
    "GT": "Guanajuato",
    "HG": "Hidalgo",
    "JA": "Jalisco",
    "MI": "Michoacan",
    "MO": "Morelos",
    "NA": "Nayarit",
    "NL": "Nuevo Leon",
    "OA": "Oaxaca",
    "PU": "Puebla",
    "QR": "Quintana Roo",
    "QT": "Queretaro",
    "SI": "Sinaloa",
    "SL": "San Luis Potosi",
    "SO": "Sonora",
    "TB": "Tabasco",
    "TL": "Tlaxcala",
    "TM": "Tamaulipas",
    "VE": "Veracruz",
    "YU": "Yucatan",
    "ZA": "Zacateca",
}


class AlliedUniversalSpider(scrapy.Spider):
    name = "allied_universal"
    allowed_domains = ["www.aus.com"]
    item_attributes = {"brand": "Allied Universal", "brand_wikidata": "Q4732537"}
    start_urls = ("https://www.aus.com/offices",)

    def parse(self, response):
        location_selectors = response.xpath('.//div[@class="Addr"]')
        for location_selector in location_selectors[:]:
            yield from self.parse_location(location_selector)

    def parse_location(self, location):
        ref = (
            location.xpath('.//div[@class="Address-1"]/text()').extract_first().strip()
        )
        street_address = (
            location.xpath('.//div[@class="Address-1"]/text()').extract_first().strip()
            + ", "
            + location.xpath('.//div[@class="Address-2"]/text()')
            .extract_first()
            .strip()
        )
        postcode = (
            location.xpath('.//span[@class="Zip"]/text()').extract_first().strip()
        )
        city = location.xpath('.//span[@class="City"]/text()').extract_first().strip()
        state = location.xpath('.//span[@class="State"]/text()').extract_first().strip()
        country = (
            location.xpath('.//div[@class="Country"]/text()').extract_first().strip()
        )
        if not country:
            country = "USA"
            if state in USA_STATES:
                state = USA_STATES[state]
        elif country == "Mexico":
            if state in MEXICO_STATES:
                state = MEXICO_STATES.get(state)
        phone = (
            location.xpath('.//div[@class="PhoneNum"]/text()')
            .extract_first()
            .replace(".", "-")
            .strip()
        )
        website = location.xpath(".//a/@href").extract_first()
        if website:
            if website[0] == "/":
                website = "https://www.aus.com" + website
        addr_full = street_address + ", " + state + ", " + postcode
        properties = {
            "ref": ref,
            "street_address": street_address,
            "postcode": postcode,
            "city": city,
            "state": state,
            "country": country,
            "phone": phone,
            "addr_full": addr_full,
            "website": website,
        }
        yield GeojsonPointItem(**properties)
