from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class ChilisKWSpider(Spider):
    name = "chilis_kw"
    item_attributes = {"brand": "Chili's", "brand_wikidata": "Q1072948"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "HTTPERROR_ALLOWED_CODES": [500]}
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        gql_query = """
{"query":" query ($subdomain: String!, $id: ID) { store(subdomain: $subdomain) { id branches(id: $id) { id titleAr titleEn addressAr addressEn areaEn contactNumber phoneNumber  lat lng openingHours } } }","variables":{"subdomain":"chiliskuwait"}}"""
        yield Request(
            url="https://graphql-prod.stellate.sh/graphql",
            method="POST",
            body=gql_query,
        )

    def parse(self, response):
        for location in response.json()["data"]["store"]["branches"]:
            item = DictParser.parse(location)
            for day in location["openingHours"]:
                day_name = day["day"].capitalize()
                open_time = day["open-at"]
                close_time = day["close-at"]
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_range(day=DAYS_EN[day_name], open_time=open_time, close_time=close_time)

            apply_category(Categories.RESTAURANT, item)
            yield item
