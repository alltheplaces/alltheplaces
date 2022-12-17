import json

import scrapy

from locations.linked_data_parser import LinkedDataParser


class MercureEuSpider(scrapy.Spider):
    name = "mercure_eu"
    item_attributes = {"brand": "Mercure", "brand_wikidata": "Q87410393"}
    start_urls = [
        'https://liveapi.yext.com/v2/accounts/1624327134898036854/entities?api_key=f60a800cdb7af0904b988d834ffeb221&v=20160822&filter={"$or":[{"meta.id":{"$eq":"Mercure+-+PAT"}},{"meta.id":{"$eq":"Mercure+-+PBE"}},{"meta.id":{"$eq":"Mercure+-+PCH"}},{"meta.id":{"$eq":"Mercure+-+PCZ"}},{"meta.id":{"$eq":"Mercure+-+PDE"}},{"meta.id":{"$eq":"Mercure+-+PES"}},{"meta.id":{"$eq":"Mercure+-+PFR"}},{"meta.id":{"$eq":"Mercure+-+PGB"}},{"meta.id":{"$eq":"Mercure+-+PGE"}},{"meta.id":{"$eq":"Mercure+-+PGR"}},{"meta.id":{"$eq":"Mercure+-+PHU"}},{"meta.id":{"$eq":"Mercure+-+PIT"}},{"meta.id":{"$eq":"Mercure+-+PKZ"}},{"meta.id":{"$eq":"Mercure+-+PLT"}},{"meta.id":{"$eq":"Mercure+-+PLU"}},{"meta.id":{"$eq":"Mercure+-+PLV"}},{"meta.id":{"$eq":"Mercure+-+PMC"}},{"meta.id":{"$eq":"Mercure+-+PMK"}},{"meta.id":{"$eq":"Mercure+-+PMT"}},{"meta.id":{"$eq":"Mercure+-+PNL"}},{"meta.id":{"$eq":"Mercure+-+PPL"}},{"meta.id":{"$eq":"Mercure+-+PPT"}},{"meta.id":{"$eq":"Mercure+-+PRO"}},{"meta.id":{"$eq":"Mercure+-+PRU"}},{"meta.id":{"$eq":"Mercure+-+PTR"}},{"meta.id":{"$eq":"Mercure+-+PUA"}},{"meta.id":{"$eq":"Mercure+-+PUZ"}}]}&languages=en&limit=50'
    ]
    custom_settings = {"URLLENGTH_LIMIT": 6000}

    def parse(self, response):
        countries = response.json().get("response").get("entities")
        for country in countries:
            areas = country.get("c_mercurePDCountryToChildRDCLink")
            url = 'https://liveapi.yext.com/v2/accounts/1624327134898036854/entities?api_key=f60a800cdb7af0904b988d834ffeb221&v=20160822&filter={"$or":['
            for area in areas:
                url += f"{{\"meta.id\":{{\"$eq\":\"{area.replace(' ', '+')}\"}}}},"
            url = url[:-1] + "]}&languages=en&limit=50"
            yield scrapy.Request(url=url, callback=self.parse_city)

    def parse_city(self, response):
        city = response.json().get("response").get("entities")
        for hotels in city:
            hotels_id = hotels.get("c_mercurePDCityToChildHotelLink")
            if not hotels_id:
                hotels_id = hotels.get("c_mercurePDRegionToChildHotelLink")
            for hotel_id in hotels_id:
                url = f"https://all.accor.com/hotel/{hotel_id}/index.en.shtml"
                yield scrapy.Request(url=url, callback=self.parse_hotel_detail)

    def parse_hotel_detail(self, response):
        data = response.xpath("/html/head/text()").get().strip()
        if data == "" or not json.loads(data).get("address"):
            data = response.xpath("/html/head/script[13]/text()").get()
        if data == "" or not json.loads(data).get("address"):
            data = response.xpath("/html/head/script[14]/text()").get()

        if data:
            data_json = json.loads(data)
            item = LinkedDataParser.parse_ld(data_json)
            item["name"] = data_json.get("legalName")
            item["ref"] = response.url.replace("https://all.accor.com/hotel/", "").replace("/index.en.shtml", "")

        yield item
