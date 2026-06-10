from locations.spiders.clas_ohlson_no import ClasOhlsonNOSpider


class FakeResponse:
    meta = {"page": 0}

    def json(self):
        return {
            "total": 1,
            "data": [
                {
                    "url": "/store/241?lat=60.47&long=8.46",
                    "phone": "",
                    "latitude": "60.9713476",
                    "longitude": "9.2864463",
                    "storeMapIcon": "/medias/sys_master/StoreLocator/9548256083998.jpg",
                    "storeContact": "23 21 40 00",
                    "storeTimings": {
                        "Mandager": "10:00 - 20:00",
                        "Tirsdager": "10:00 - 20:00",
                        "Onsdager": "10:00 - 20:00",
                        "Torsdager": "10:00 - 20:00",
                        "Fredager": "10:00 - 20:00",
                        "Lørdager": "10:00 - 18:00",
                        "Søndager": "Stengt",
                    },
                    "storeAddresses": {
                        "SalesChannelAddressId": "2_241",
                        "SalesChannelName": "Leira, Alti Valdres",
                        "SalesChannelAddressType": "Visitor",
                        "SalesChannelAddress": "Clas Ohlson AS Leira<br />Markaveien 15<br />2920 Leira",
                    },
                }
            ],
        }


def test_parse_store_payload():
    spider = ClasOhlsonNOSpider()
    items = list(spider.parse(FakeResponse()))

    assert len(items) == 1
    item = items[0]
    assert item["ref"] == "2_241"
    assert item["branch"] == "Leira, Alti Valdres"
    assert item["street_address"] == "Markaveien 15"
    assert item["postcode"] == "2920"
    assert item["city"] == "Leira"
    assert item["country"] == "NO"
    assert item["phone"] == "23 21 40 00"
    assert item["website"] is None
    assert item["lat"] == "60.9713476"
    assert item["lon"] == "9.2864463"
    assert item["image"] == "https://www.clasohlson.com/medias/sys_master/StoreLocator/9548256083998.jpg"
    assert item["opening_hours"].as_opening_hours() == "Mo-Fr 10:00-20:00; Sa 10:00-18:00; Su closed"
