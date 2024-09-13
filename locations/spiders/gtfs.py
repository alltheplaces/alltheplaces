from io import BytesIO
from zipfile import ZipFile

from scrapy import Request
from scrapy.spiders import CSVFeedSpider
from scrapy.utils.iterators import csviter

from locations.categories import Extras, apply_category, apply_yes_no
from locations.items import Feature

BRAND_MAPPING = {
    "Calgary Transit": {
        "network": "CTrain",
        "network:wikidata": "Q1022321",
        "operator": "Calgary Transit",
        "operator:wikidata": "Q143630",
    },
    "Casco Bay Lines": {
        "network": "Casco Bay Lines",
        "network:wikidata": "Q5048264",
        "operator": "Casco Bay Lines",
        "operator:wikidata": "Q5048264",
    },
    "Fertagus": {"operator": "Fertagus", "operator:wikidata": "Q1408210"},
    "Grand River Transit": {
        "network": "Ion",
        "network:wikidata": "Q106676138",
        "operator": "Grand River Transit",
        "operator:wikidata": "Q3459117",
    },
    "Metro Transit": {
        "network": "Metro Transit",
        "network:wikidata": "Q3307442",
        "operator": "Metro Transit",
        "operator:wikidata": "Q3307442",
    },
    "Société de transport de Montréal": {
        "network": "Métro de Montréal",
        "network:wikidata": "Q392377",
        "operator": "Société de transport de Montréal",
        "operator:wikidata": "Q1817151",
    },
    "South Shore Line": {
        "network": "NICTD",
        "network:wikidata": "Q31313",
        "operator": "NICTD",
        "operator:wikidata": "Q31313",
    },
    "Taichung": {
        "network": "臺中捷運",
        "network:wikidata": "Q5972247",
        "operator": "臺中捷運公司",
        "operator:wikidata": "Q17370558",
    },
    "Toronto Transit Commission": {
        "network": "Toronto subway",
        "network:wikidata": "Q20379",
        "operator": "Toronto Transit Commission",
        "operator:wikidata": "Q17978",
    },
    "Trenes Argentinos": {
        "network": "Mitre",
        "network:wikidata": "Q3239158",
        "operator": "Trenes Argentinos Operadora Ferroviaria",
        "operator:wikidata": "Q6116255",
    },
    "Warrington's Own Buses": {
        "network": "Warrington's Own Buses",
        "network:wikidata": "Q7000937",
        "operator": "Warrington's Own Buses",
        "operator:wikidata": "Q7000937",
    },
}


class GTFSSpider(CSVFeedSpider):
    name = "gtfs"
    start_urls = ["https://bit.ly/catalogs-csv"]
    no_refs = True

    def parse_row(self, response, row):
        if row["status"] not in ("active", ""):
            return
        if row["data_type"] != "gtfs":
            return
        feed_attributes = {
            "country": row["location.country_code"],
            "state": row["location.subdivision_name"],
            "city": row["location.municipality"],
            "operator": row["provider"],
            "extras": {},
        }

        brand_tags = BRAND_MAPPING.get(row["provider"], {})
        if "operator" in brand_tags:
            feed_attributes["operator"] = brand_tags["operator"]
        if "operator:wikidata" in brand_tags:
            feed_attributes["operator_wikidata"] = brand_tags["operator:wikidata"]
        if "network" in brand_tags:
            feed_attributes["extras"]["network"] = brand_tags["network"]
        if "network:wikidata" in brand_tags:
            feed_attributes["extras"]["network_wikidata"] = brand_tags["network:wikidata"]

        url = row["urls.latest"] or row["urls.direct_download"]
        self.logger.info("Provider: %s URL: %s", row["provider"], url)
        if url is not None:
            yield Request(url, self.parse_zip, cb_kwargs={"feed_attributes": feed_attributes})

    def parse_zip(self, response, feed_attributes):
        z = ZipFile(BytesIO(response.body))
        if "stops.txt" not in z.namelist():
            return

        agencies = {}
        if "agency.txt" in z.namelist():
            for row in csviter(z.read("agency.txt")):
                if row.get("agency_id"):
                    agencies[row["agency_id"]] = {"network": row.get("agency_name")}
                else:
                    feed_attributes["extras"]["network"] = row.get("agency_name")

        # Feed publisher is sometimes the transit agency, but more often the publishing service they use
        if 0 and "feed_info.txt" in z.namelist():
            for row in csviter(z.read("feed_info.txt")):
                if row.get("feed_publisher_name"):
                    feed_attributes["operator"] = row["feed_publisher_name"]

        if "attributions.txt" in z.namelist():
            for row in csviter(z.read("attributions.txt")):
                if row.get("is_operator") == "1" or row.get("is_authority") == "1":
                    feed_attributes["operator"] = row.get("organization_name")

        feed_attributes = {k: v for k, v in feed_attributes.items() if v}

        levels = {}
        if "levels.txt" in z.namelist():
            for row in csviter(z.read("levels.txt")):
                if "level_id" in row:
                    levels[row["level_id"]] = {"level": row.get("level_index"), "level:ref": row.get("level_name")}

        stop_routes = {}
        if "stop_times.txt" in z.namelist() and "trips.txt" in z.namelist() and "routes.txt" in z.namelist():
            routes = {route.get("route_id"): route for route in csviter(z.read("routes.txt"))}
            trips = {trip.get("trip_id"): trip for trip in csviter(z.read("trips.txt"))}
            for stop_time in csviter(z.read("stop_times.txt")):
                trip = trips.get(stop_time.get("trip_id"))
                if not trip:
                    continue
                stop_id = stop_time.get("stop_id")
                route = routes.get(trip.get("route_id"))
                if stop_id in stop_routes:
                    stop_routes[stop_id].append(route)
                else:
                    stop_routes[stop_id] = [route]

        stopsdata = z.read("stops.txt")
        stop_id_names = {
            row["stop_id"]: row["stop_name"] for row in csviter(stopsdata) if "stop_id" in row and "stop_name" in row
        }
        # TODO: Localized (stop, agency) names from translations.txt
        for row in csviter(stopsdata):
            yield from self.parse_stop(response, row, levels, agencies, stop_id_names, stop_routes, feed_attributes)

    def parse_stop(self, response, row, levels, agencies, stop_id_names, stop_routes, feed_attributes):
        if not row.get("stop_lat") or not row.get("stop_lon"):
            return

        if row.get("location_type") == "3":
            # "Generic Node," only used for pathways
            return

        routes = stop_routes.get(row.get("stop_id"), [])
        item = Feature(feed_attributes)
        item["ref"] = row.get("stop_code")
        item["name"] = row.get("stop_name")
        item["lat"] = float(row.get("stop_lat"))
        item["lon"] = float(row.get("stop_lon"))
        item["website"] = row.get("stop_url")
        item["located_in"] = stop_id_names.get(row.get("parent_station"))
        item["extras"]["gtfs_id"] = row.get("stop_id")
        item["extras"]["name:pronunciation"] = row.get("tts_stop_name")
        item["extras"]["description"] = row.get("stop_desc")
        item["extras"]["loc_ref"] = row.get("platform_code")
        item["extras"].update(levels.get(row.get("level_id"), {}))

        for route in routes:
            agency = agencies.get(route.get("agency_id"), {})
            for k, v in agency.items():
                item["extras"][k] = ";".join(filter(None, set((item["extras"].get(k, "").split(";")) + [v])))

        apply_yes_no(
            Extras.WHEELCHAIR, item, row.get("wheelchair_boarding") == "1", row.get("wheelchair_boarding") != "2"
        )

        route_types = {route.get("route_type") for route in routes}
        if row.get("location_type") == "1":
            apply_category({"public_transport": "station"}, item)
            if not route_types.isdisjoint({"0", "1", "2", "5", "7", "12"}):
                apply_category({"railway": "station"}, item)
            if not route_types.isdisjoint({"3", "11"}):
                apply_category({"amenity": "bus_station"}, item)
            if "4" in route_types:
                apply_category({"amenity": "ferry_terminal"}, item)
            if "6" in route_types:
                apply_category({"aerialway": "station"}, item)
        elif row.get("location_type") == "2":
            apply_category({"entrance": "yes"}, item)
            if "1" in route_types:
                apply_category({"railway": "subway_entrance"}, item)
            if not route_types.isdisjoint({"0", "2", "5", "7", "12"}):
                apply_category({"railway": "train_station_entrance"}, item)
        else:
            apply_category({"public_transport": "platform"}, item)
            if not route_types.isdisjoint({"0", "1", "2", "5", "7", "12"}):
                apply_category({"railway": "platform"}, item)
            if not route_types.isdisjoint({"3", "11"}):
                apply_category({"highway": "bus_stop"}, item)
            if "4" in route_types:
                apply_category({"amenity": "ferry_terminal"}, item)
            if "6" in route_types:
                apply_category({"aerialway": "station"}, item)

        item["extras"] = {k: v for k, v in item["extras"].items() if v}
        yield item
