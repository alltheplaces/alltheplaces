from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class EspacolaserBRSpider(JSONBlobSpider):
    name = "espacolaser_br"
    item_attributes = {
        "brand": "Espaçolaser",
        "brand_wikidata": "Q112326409",
    }
    start_urls = [
        "https://func-prd-ecom-svc-ecm-el.azurewebsites.net/api/espacolaser/pt-BR/GetEstablishments?lat=-34&lng=138&appChannel=ECM_SL_BRA&skip=0&code=0FRo43/d4a16aXUWaJIc0sTUK58L2jyZCat2VWG8P9IUEwguAmpzNw=="
    ]

    def extract_json(self, response):
        return response.json()["list"]

    def post_process_item(self, item, response, location):
        # {'Id': 488, 'FatherId': 379, 'Description': 'RS - PORTO ALEGRE - SARANDI ESPACOLASER', 'AddressLat': -29.9993391, 'AddressLng': -51.1312627,
        # 'AppChannels': [{'channel': 'ECM_BRA'}, {'channel': 'LP_BRA'}, {'channel': 'APP_AGE'}, {'channel': 'ECM_SL_BRA'}, {'channel': 'ECM_AGE'}, {'channel': 'WPP_BRA'}],
        # 'Address': {'PostalCode': '91130-720', 'Type': 'git digit ', 'Description': 'SERTÓRIO', 'StateAbrev': 'RS', 'City': 'PORTO ALEGRE',
        # 'Neighborhood': 'SARANDI', 'Number': '8000', 'Complement': None}, 'SchedulerCalendarTime': [{'StartTime': '14:00', 'EndTime': '20:00', 'DaysOfWeek': [0]}, {'StartTime': '9:00', 'EndTime': '22:00', 'DaysOfWeek': [1, 2, 3, 4, 5, 6]}],
        # 'Phones': [{'Number': '+55 (51) 30181484', 'Type': 'Commercial'}, {'Number': '+55 (51) 996440964', 'Type': 'WhatsappPhone'}],
        # 'Resources': [{'Id': 3, 'Description': 'ALEXANDRITE', 'Inactive': False, 'IsEquipment': True, 'IsScheduler': False, 'Quantity': 1}],
        # 'Emails': ['poa-centerlar@espacolaser.com.br'], 'SchedulerResourceClassifier': 2, 'MaximumNumberOfDaysForScheduling': 90}
        item["email"] = location["Emails"][0]
        item["lat"] = location["AddressLat"]
        item["lon"] = location["AddressLng"]
        item["phone"] = location["Phones"][0]["Number"]  # TODO: Make more robust to select type=Commercial

        oh = OpeningHours()
        for rule in location["SchedulerCalendarTime"]:
            for day in rule["DaysOfWeek"]:
                oh.add_range(DAYS[day], rule["StartTime"], rule["EndTime"])
        item["opening_hours"] = oh
        yield item
