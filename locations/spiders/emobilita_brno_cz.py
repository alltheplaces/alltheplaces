import scrapy

from locations.items import Feature


class EmobilitaBrnoCzSpider(scrapy.Spider):
    name = "emobilita_brno_cz"
    item_attributes = {"operator": "Teplárny Brno", "operator_wikidata": "Q54980987"}

    def start_requests(self):
        url = "https://uuapp.plus4u.net/uu-chargeup-portalg01/cde72fa6c93d4cad87dcfd67ed8fc975/chargingPlace/listWithinPolygon"
        payload = '{"criteria":{"connectors":[],"onlyAvailable":false,"dataSources":[],"powerFrom":0},"northEast":{"lat":50,"lng":17},"southWest":{"lat":49,"lng":18}}'
        headers = {"Content-Type": "application/json; charset=utf-8"}

        yield scrapy.http.Request(url, self.parse, method="POST", headers=headers, body=payload)

    def parse(self, response):
        result = response.json()

        for stations in result["chargingPlaces"]["itemList"]:
            for station in stations["chargingStations"]:
                if station["state"] != "VALID":
                    continue

                evse = [point["evseId"] for point in station["chargingPoints"]]
                connectors = [point["connectors"]["types"][0]["key"] for point in station["chargingPoints"]]
                mennekes = connectors.count("Mennekes")
                ccs2 = connectors.count("CCS2")

                item = Feature()
                item["name"] = station["name"]
                item["lon"] = station["location"]["coordinates"][0]
                item["lat"] = station["location"]["coordinates"][1]
                item["ref"] = station["stationCode"]
                item["extras"]["ref:EU:EVSE"] = ";".join(evse)
                if mennekes:
                    item["extras"]["socket:type2"] = mennekes
                if ccs2:
                    item["extras"]["socket:type2_combo"] = ccs2
                item["extras"]["capacity"] = max(mennekes, ccs2)

            yield item
