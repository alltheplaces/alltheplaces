import scrapy
from locations.dict_parser import DictParser

class TitleBoxingClubUSSpider(scrapy.Spider):
    name = "title_boxing_club_us"
    item_attributes = {"brand": "Title Boxing Club", "brand_wikidata": "Q126391325"}
    start_urls = ["https://api.hubapi.com/cms/v3/hubdb/tables/121868642/rows?portalId=48754936"]
    custom_settings = {"ROBOTSTXT_OBEY": False}


    def parse(self, response):
        for poi in response.json()["results"]:
            poi["values"]["street_address"] = poi["values"].pop("address")
            item = DictParser.parse(poi['values'])    
            item["website"] = "https://www.titleboxingclub.com/location/" + poi["values"]["site_slug"]
            item["name"] = "Title Boxing Club"
            yield item
