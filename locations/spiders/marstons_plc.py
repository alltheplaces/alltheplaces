import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature


class MarstonsPlcSpider(scrapy.Spider):
    name = "marstons_plc"
    item_attributes = {"brand": "Marston's", "brand_wikidata": "Q6773982"}
    allowed_domains = ["marstonspubs.co.uk"]
    store_types = {}

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.marstonspubs.co.uk/ajax/finder/markers/",
            callback=self.parse_store_ids,
        )

    def parse_store_ids(self, response):
        store_ids = response.json()
        ids = []

        for id in store_ids["markers"]:
            self.store_types[id["i"]] = id["t"]
            ids.append(id["i"])

        count = 1
        params = ""

        ## Adding all the ids together makes the url too large
        for i in ids:
            if count < 47:
                params = params + "p=" + str(i)
                params = params + "&"
            else:
                url = "https://www.marstonspubs.co.uk/ajax/finder/outlet/?"
                params = params[:-1]
                url = url + params
                count = 0
                params = ""
                yield scrapy.Request(url, callback=self.parse)
            count += 1

        url = "https://www.marstonspubs.co.uk/ajax/finder/outlet/?"
        params = params[:-1]
        url = url + params
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        data = response.json()
        places = data["outlets"]

        for place in places:
            address = place["address"]
            city = place["town"].split(",")
            addr = address.split(", ")
            if len(addr) == 4:
                str_addr = addr[0]
                state = addr[2]
                postal = addr[3]
            elif len(addr) == 3:
                str_addr = addr[0]
                state = ""
                postal = addr[2]
            elif len(addr) == 5:
                str_addr = addr[0]
                state = addr[3]
                postal = addr[4]
            elif len(addr) == 6:
                str_addr = addr[0]
                state = addr[4]
                postal = addr[5]

            properties = {
                "ref": place["phc"],
                "name": place["name"],
                "addr_full": address,
                "street_address": str_addr,
                "city": city[0],
                "state": state,
                "postcode": postal,
                "country": "GB",
                "lat": place["lat"],
                "lon": place["lng"],
                "phone": place["tel"],
                "website": place["url"],
                "email": place["email"],
                "brand": place["pfLabel"],
            }
            apply_category(Categories.PUB, properties)
            apply_yes_no("payment:marstons_privilege_card", properties, place["sv"], False)

            if img := place.get("img"):
                properties["image"] = "https://www.marstonspubs.co.uk" + img

            if self.store_types[place["phc"]] == 2:
                apply_category(Categories.HOTEL, properties)

            yield Feature(**properties)
