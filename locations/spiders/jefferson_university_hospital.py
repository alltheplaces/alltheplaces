import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class JeffersonUniversityHospitalSpider(scrapy.Spider):
    name = "jefferson_university_hospital"
    item_attributes = {
        "brand": "Jefferson University Hospital",
        "brand_wikidata": "Q59676202",
    }
    allowed_domains = ["jeffersonhealth.org", "jeffersonhealth-prod.searchstax.com"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False, "REDIRECT_ENABLED": False}

    def start_requests(self):
        url = "https://jeffersonhealth-prod.searchstax.com/solr/jh-prod/search-name-location?rows=10&start=0&fq=content_type:health2021/content-type/location"
        headers = {"Authorization": "Basic amgtcHJvZC1yZWFkb25seTpjMyoyZEpOdm1jYVRReTch"}
        yield scrapy.Request(url=url, headers=headers, callback=self.get_number_locations)

    def get_number_locations(self, response):
        numbers_locations = response.json().get("response", {}).get("numFound")
        url = f"https://jeffersonhealth-prod.searchstax.com/solr/jh-prod/search-name-location?rows={numbers_locations}&start=0&fq=content_type:health2021/content-type/location"
        headers = {"Authorization": "Basic amgtcHJvZC1yZWFkb25seTpjMyoyZEpOdm1jYVRReTch"}
        yield scrapy.Request(url=url, headers=headers, callback=self.get_details_location)

    def get_details_location(self, response):
        domain = "https://www.jeffersonhealth.org"
        for url in response.json().get("response", {}).get("docs", {}):
            yield scrapy.Request(url=f'{domain}{url.get("page_url")}.model.json', callback=self.parse_location)

    def parse_location(self, response):
        location_data = response.json().get("locationLinkingData")
        item = DictParser.parse(response.json().get("locationLinkingData"))
        item["ref"] = item["website"]

        if item["name"] == item["street_address"]:
            item["name"] = f"{location_data['parentOrganization']} {location_data['@type']} at {item.get('city')}"
            self.crawler.stats.inc_value("jefferson_univ_hosp/name_is_same_as_address")

        apply_category(Categories.CLINIC, item)
        yield item
