import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


# See https://www.marriott.com/marriott-brands.mi for an explanation of the world of Marriott brands.
# Of the sites below Ritz Carlton is probably the most important.
# TODO: ["Ritz-Carlton", "Q782200"] will needs its own site spider?
# TODO: ["JW Marriott Hotels", "Q1067636"] will need its own site spider?
# TODO: ["Renaissance Hotels", "Q2143252"] will need its own site spider?
# TODO: ["Gaylord Hotels", "Q3099664"] will need its own site spider? (convention centres)
# TODO: ["Protea Hotels", "Q17092570"] will need its own site spider?
# TODO: ["Edition Hotels", "Q91218404"] will need its own site spider?
# There are other ways in:
# 'https://aloft-hotels.marriott.com/locations/'
# 'https://four-points.marriott.com/hotel-directory/'
# 'https://w-hotels.marriott.com/destinations/'
# 'https://le-meridien.marriott.com/hotel-directory/'
# 'https://sheraton.marriott.com/destinations/'
# 'https://courtyard.marriott.com/destinations/'
# 'https://westin.marriott.com/hotel-locations/'
# 'https://st-regis.marriott.com/hotel-directory/'
# 'https://fairfield.marriott.com/locations/'
class MarriottHotelsSpider(scrapy.Spider):
    name = "marriott"
    custom_settings = {"REDIRECT_ENABLED": False}
    download_delay = 2.0

    # Continue policy of ignoring collection hotels for now.
    my_brands = {
        "MC": ["Marriott Hotels & Resorts", "Q3918608"],
        "AR": ["AC Hotels", "Q5653536"],
        "AK": "ignore",  # Autograph Collection
        "AL": ["Aloft Hotels", "Q4734166"],
        "CY": ["Courtyard by Marriott", "Q1053170"],
        "DE": ["Delta Hotels", "Q5254663"],
        "DS": ["Design Hotels", "Q5264274"],
        "EL": ["Element Hotels", "Q91948072"],
        "FI": ["Fairfield by Marriott", "Q5430314"],
        "FP": ["Four Points by Sheraton", "Q1439966"],
        "LC": "ignore",  # Luxury Collection
        "MD": ["Le Méridien", "Q261077"],
        "OX": ["Moxy Hotels", "Q70287020"],
        "RI": ["Residence Inn by Marriott", "Q7315394"],
        "SI": ["Sheraton Hotels and Resorts", "Q634831"],
        "SH": ["SpringHill Suites", "Q7580351"],
        "TX": "ignore",  # Tribute Portfolio
        "XR": ["St. Regis Hotels & Resorts", "Q30715430"],
        "TS": ["Townplace Suites by Marriott", "Q7830092"],
        "WH": ["W Hotels", "Q7958488"],
        "WI": ["Westin Hotels & Resorts", "Q1969162"],
    }

    def start_requests(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVXYZ"
        # Generate all possible Marriott brand codes.
        for x in letters:
            for y in letters:
                url = "https://pacsys.marriott.com/data/marriott_properties_{}_en-US.json".format(x + y)
                yield scrapy.Request(url, callback=self.parse_brand_json)

    def parse_brand_json(self, response):
        for cities in DictParser.iter_matching_keys(response.json(), "city_properties"):
            for hotel in cities:
                yield self.parse_hotel(hotel)

    def parse_hotel(self, hotel):
        brand = self.my_brands.get(hotel["brand_code"])
        if not brand:
            self.logger.error("unknown brand: %s", hotel["brand_code"])
            return None
        if brand == "ignore":
            return None
        hotel["street_address"] = hotel.pop("address")
        item = DictParser.parse(hotel)
        item["website"] = "https://www.marriott.com/" + hotel["marsha_code"]
        item["ref"] = hotel["marsha_code"]
        item["image"] = hotel.get("exterior_photo")
        item["brand"], item["brand_wikidata"] = brand
        apply_category(Categories.HOTEL, item)
        return item
