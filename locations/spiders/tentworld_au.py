from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class TentworldAUSpider(JSONBlobSpider):
    name = "tentworld_au"
    item_attributes = {"brand": "Tentworld", "brand_wikidata": "Q117747711", "extras": Categories.SHOP_OUTDOOR.value}
    start_urls = [
        "https://mcprod.tentworld.com.au/graphql?query=query+storeAvailability%28%24currentPage%3AInt%3D1%24distance%3ASortEnum%3DASC%24isCurrentLocation%3ABoolean%24radius%3AInt%21%24search_term%3AString%21%24findInStore%3ABoolean%21%24pageSize%3AInt%3D3%24skus%3A%5BStoreLocationsItemQuantityInput%21%5D%21%29%7BstoreAvailability%28area%3A%7Bradius%3A%24radius+search_term%3A%24search_term%7DcurrentPage%3A%24currentPage+isCurrentLocation%3A%24isCurrentLocation+sort%3A%7Bdistance%3A%24distance%7DfindInStore%3A%24findInStore+pageSize%3A%24pageSize+skus%3A%24skus%29%7Bitems%7Blocation%7Bcity+contact_name+country_id+description+distance+email+name+pickup_location_code+phone+postcode+region+region_id+street+url_key+__typename%7DlocationAvailabilityStatus+skuAvailability%7Bquantity+sku+stockAvailabilityStatus+__typename%7D__typename%7Dpage_info%7Bcurrent_page+page_size+total_pages+__typename%7D__typename%7D%7D&operationName=storeAvailability&variables=%7B%22currentPage%22%3A1%2C%22distance%22%3A%22ASC%22%2C%22pageSize%22%3A50%2C%22findInStore%22%3Atrue%2C%22isCurrentLocation%22%3Afalse%2C%22radius%22%3A4000%2C%22search_term%22%3A%22%22%2C%22skus%22%3A%5B%5D%7D"
    ]
    locations_key="location"
    custom_settings = {
        "ROBOTSTXT_OBEY": False
    }

    def extract_json(self, response):
        locations = []
        for item in response.json()["data"]["storeAvailability"]["items"]:
            locations.append(item["location"])
        return locations

    def pre_process_data(self, location: dict):
        location["id"] = location["url_key"]