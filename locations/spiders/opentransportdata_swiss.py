import csv
import datetime
import io
import zipfile
from collections import namedtuple

import scrapy

from locations.items import Feature

# To emit proper OpenStreetMap tags for platforms, we need to keep some
# per-station properties in memory.
Station = namedtuple("Station", "name operator city country means")


class OpentransportdataSwissSpider(scrapy.Spider):
    name = "opentransportdata_swiss"
    allowed_domains = ["opentransportdata.swiss"]
    dataset_attributes = {
        "attribution": "required",
        "attribution:name": "OpenTransportData.swiss",
        "attribution:wikidata": "Q97319754",
        "license:website": "https://opentransportdata.swiss/en/terms-of-use/",
        "use:commercial": "yes",
        "use:openstreetmap": "yes",
        "website": "https://opentransportdata.swiss/",
    }

    dataset_pattern = "https://opentransportdata.swiss/en/dataset/%s/permalink"

    def start_requests(self):
        url = "https://opentransportdata.swiss/de/dataset/bfr-rollstuhl"
        yield scrapy.Request(url, callback=self.handle_wheelchair_overview)

    def handle_wheelchair_overview(self, response):
        # The download URL changes daily with every database dump.
        h = response.xpath("//a[@download='BfR_Haltestellendaten.csv']/@href")
        yield scrapy.Request(h.get(), callback=self.handle_wheelchair_data)

    def handle_wheelchair_data(self, response):
        # The data feed supplies seperate properties for railbound
        # and non-railbound wheelchair accessibility; in remote areas,
        # there are stations whose railway platforms are fully accessible
        # but some bus platforms haven’t yet been reconstructed to conform
        # with present-day accessibility standards. However, at this time
        # in our fetching process, we haven’t yet retrieved the full station
        # table, so we don’t yet know what means of transportations are
        # relevant. Therefore, we keep separate values for rail vs non-rail
        # wheelchair accessibility, and merge the data only later, when we
        # have fetched all data.
        #
        # The data feed sometimes supplies multiple values for wheelchair
        # accessibility, each with an optional start and end date.
        # For example, a particular platform may undergo construction
        # and still be operational during that time, although only with
        # limited accessibility for wheelchairs.
        self.wheelchair_accessible = {}
        for row in self.read_csv("bfr_haltestellendaten", response):
            sloid = row["sloid"]
            start_date = self.parse_date(row.get("gültigVon"))
            end_date = self.parse_date(row.get("gültigBis"))
            # sg = "schienengebunden" = railbound
            if row["sg_Autonomie"] == "1":
                railbound_value = "yes"
            elif row["sg_Rampeneinsatz"] == "1":
                railbound_value = "limited"
            else:
                railbound_value = "no"
            # ug = "ungebunden" = non-railbound
            if row["ug_Autonomie"] == "1":
                nonrailbound_value = "yes"
            elif row["ug_Rampeneinsatz"] == "1":
                nonrailbound_value = "limited"
            else:
                nonrailbound_value = "no"
            self.wheelchair_accessible.setdefault(sloid, []).append(
                (start_date, end_date, railbound_value, nonrailbound_value)
            )
        # Next, fetch data file for wheelchair-accessible toilets.
        url = self.dataset_pattern % "prm-toilet-actual-date"
        yield scrapy.Request(url, callback=self.handle_wheelchair_toilets)

    def handle_wheelchair_toilets(self, response):
        self.toilets_wheelchair = {}  # "ch:1:sloid:2213" -> "yes"
        for row in self.read_csv("actual-date-toilet", response):
            status = row["status"]
            sloid = row["parentSloidServicePoint"]
            value = {
                "NO": "no",
                "PARTIAL": "limited",
                "YES": "yes",
            }.get(row["wheelchairToilet"])
            if status == "VALIDATED" and sloid and value:
                self.toilets_wheelchair[sloid] = value
        self.logger.info(
            f"found {len(self.toilets_wheelchair)} " + "transit stations with wheelchair toilet attributes"
        )
        # Next, fetch data file for "service points" (stations/stop areas).
        url = self.dataset_pattern % "service-points-actual-date"
        yield scrapy.Request(url, callback=self.handle_service_points)

    def handle_service_points(self, response):
        self.stations = {}
        # "swiss-only" is an misnomer; the actual data goes far beyond.
        for row in self.read_csv("actual_date-swiss-only-service_point", response):
            if row["status"] != "VALIDATED":
                continue
            sloid = row["sloid"]
            name = row["designationLong"] or row["designationOfficial"]
            operator = row["businessOrganisationDescriptionEn"]
            if any(operator.startswith(p) for p in ("Dummy_", "Fiktive ")):
                operator = ""
            city = row["localityName"] or row["municipalityName"]
            if not city and "," in name:
                city = name.split(",", 1)[0]
            country = row["isoCountryCode"]
            means = tuple(row["meansOfTransport"].split("|"))
            wheelchair, wheelchair_cond = self.wheelchair_tags(sloid, means)
            tags = {
                "public_transport": "stop_area",
                "name": name,
                "operator": operator,
                "ref:IFOPT": sloid,
                "uic_ref": self.parse_uic_ref(row),
                "wheelchair": wheelchair,
                "wheelchair:conditional": wheelchair_cond,
                "toilets:wheelchair": self.toilets_wheelchair.get(sloid),
            }
            tags.update(self.means_tags(means, platform=False))

            lat, lon, ele = self.parse_lat_lon_ele(row)
            if lat == 0.0 or lon == 0.0:
                continue
            if ele > 0:
                tags["ele:regional"] = "%.1f" % ele

            tags = {k: v for k, v in tags.items() if v}
            yield Feature(
                lat=lat,
                lon=lon,
                city=city,
                country=country,
                ref=sloid,
                extras=tags,
            )
            self.stations[sloid] = Station(
                name=name,
                operator=operator,
                city=city,
                country=country,
                means=means,
            )

        # Next, fetch data for "traffic points" (platforms).
        url = self.dataset_pattern % "traffic-points-actual-date"
        yield scrapy.Request(url, callback=self.handle_traffic_points)

    def handle_traffic_points(self, response):
        for row in self.read_csv("actual_date-world-traffic_point", response):
            # This table does not seem to have a status column,
            # so we do not check for status="VALIDATED" here.
            sloid = row["sloid"]
            station_sloid = row["parentSloid"]
            if not station_sloid and sloid.startswith("ch:1:sloid:"):
                station_sloid = ":".join(sloid.split(":")[:4])
            station = self.stations.get(station_sloid)
            if not station:
                continue

            # Surprisingly, we don’t see in the data feed what means of
            # transportation are serving the platform, so we look at the
            # station. For wheelchair accessibility, we take the data
            # of the platform but if there’s no platform-specific data
            # we fall back to the station.
            means = station.means
            wheelchair, wheelchair_cond = self.wheelchair_tags(sloid, means)
            if not wheelchair:
                wheelchair, wheelchair_cond = self.wheelchair_tags(station_sloid, means)
            tags = {
                "public_transport": "platform",
                "name": station.name,
                "operator": station.operator,
                "ref:IFOPT": sloid,
                "wheelchair": wheelchair,
                "wheelchair:conditional": wheelchair_cond,
                "toilets:wheelchair": self.toilets_wheelchair.get(sloid),
            }
            tags.update(self.means_tags(station.means, platform=True))
            lat, lon, ele = self.parse_lat_lon_ele(row)
            if lat == 0.0 or lon == 0.0:
                continue
            if ele > 0:
                tags["ele:regional"] = "%.1f" % ele
            tags = {k: v for k, v in tags.items() if v}
            yield Feature(
                lat=lat,
                lon=lon,
                city=station.city,
                country=station.country,
                ref=sloid,
                extras=tags,
            )

    @staticmethod
    def parse_date(d):
        if d and not d.startswith("9999"):
            return datetime.datetime.strptime(d, "%d.%m.%Y").date()
        else:
            return None

    @staticmethod
    def parse_lat_lon_ele(row):
        lat = round(float(row["wgs84North"] or "0.0"), 7)
        lon = round(float(row["wgs84East"] or "0.0"), 7)
        ele = float(row["height"] or "0.0")
        return lat, lon, ele

    @staticmethod
    def parse_uic_ref(row):
        num = row["number"]
        if len(num) == 7 and num.startswith(row["uicCountryCode"]):
            return num
        else:
            return None

    @staticmethod
    def means_tags(means, platform):
        if not means:
            return {}

        main = means[0]
        funicular_means = ("CABLE_CAR", "CABLE_RAILWAY")
        railway_means = ("RACK_RAILWAY", "TRAIN")
        has_funicular = any(m in means for m in funicular_means)
        has_railway = any(m in means for m in railway_means)

        tags = {
            "aerialway": "yes" if "CHAIRLIFT" in means else None,
            "bus": "yes" if "BUS" in means else None,
            "elevator": "yes" if "ELEVATOR" in means else None,
            "ferry": "yes" if "BOAT" in means else None,
            "funicular": "yes" if has_funicular else None,
            "railway": "yes" if has_railway else None,
            "tram": "yes" if "TRAM" in means else None,
            "subway": "yes" if "METRO" in means else None,
        }

        # Indicate primary means of transportation.
        primary_tags = {
            "BOAT": {"amenity": "ferry_terminal"},
            "BUS": {"highway": "bus_stop"},
            "CABLE_CAR": {"railway": "station"},
            "CABLE_RAILWAY": {"railway": "station"},
            "CHAIRLIFT": {"aerialway": "station"},
            "ELEVATOR": {"highway": "elevator"},
            "METRO": {"railway": "station"},
            "RACK_RAILWAY": {"railway": "station", "rack": "yes"},
            "TRAM": {"railway": "station"},
            "TRAIN": {"railway": "station"},
        }
        tags.update(primary_tags.get(main, {}))

        # Set tags "public_transport" and (if appropriate) "station".
        # Values for https://wiki.openstreetmap.org/wiki/Key:station
        # based on primary means of transportation supplied by feed.
        station_tags = {
            "CABLE_CAR": "funicular",
            "CABLE_RAILWAY": "funicular",
            "METRO": "subway",
            "RACK_RAILWAY": "railway",
            "TRAIN": "railway",
            "TRAM": "tram",
        }
        if platform:
            tags["public_transport"] = "platform"
        elif tags.get("railway") == "station":
            tags["public_transport"] = "station"
            tags["station"] = station_tags.get(main)
        else:
            tags["public_transport"] = "stop_area"

        return {k: v for k, v in tags.items() if v}

    def wheelchair_tags(self, sloid, means):
        """Computes the wheelchair and wheelchair:conditional tags
        for a transit station given its SLOID identifier and the available
        means of transport."""
        acc = self.wheelchair_accessible.get(sloid)
        if not acc or not means:
            return None, None
        rail_means = {"CABLE_CAR", "CABLE_RAILWAY", "METRO", "TRAIN", "TRAM"}
        has_rail = any(m in rail_means for m in means)
        has_nonrail = any(m not in rail_means for m in means)
        values = []
        for start_date, end_date, rail_value, nonrail_value in acc:
            if not start_date:
                start_date = datetime.date(1800, 1, 1)
            if not end_date:
                end_date = datetime.date(9999, 12, 31)
            if has_rail and has_nonrail:
                if rail_value == "yes" and nonrail_value == "yes":
                    combined_value = "yes"
                elif rail_value == "limited" or nonrail_value == "limited":
                    combined_value = "limited"
                else:
                    combined_value = "no"
            elif has_rail:
                combined_value = rail_value
            else:
                combined_value = nonrail_value
            values.append((start_date, end_date, combined_value))
        values.sort()
        if len(values) == 1:
            return values[0][2], None
        default_value = values[-1][2]
        cond_values = []
        for start_date, end_date, value in values:
            if value != default_value:
                start = self.format_date(start_date)
                end = self.format_date(end_date)
                cond_values.append(f"{value} @ {start} - {end}")
        return default_value, " ; ".join(cond_values)

    @staticmethod
    def format_date(d):
        # Python strftime() is localizing its months, whereas dates in
        # OpenStreetMap conditional expressions have month names in English.
        # Therefore, we do our own date formatting.
        months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        return "%04d %s %02d" % (d.year, months[d.month - 1], d.day)

    def read_csv(self, dataset, response):
        content_type = response.headers.get("Content-Type").decode("utf-8")
        if content_type.startswith("text/csv"):
            content = response.text.removeprefix("\ufeff")
            for row in csv.DictReader(io.StringIO(content), delimiter=";"):
                yield row
        elif content_type == "application/zip":
            with zipfile.ZipFile(io.BytesIO(response.body)) as feed_zip:
                filenames = [n for n in feed_zip.namelist() if n.startswith(dataset + "-") and n.endswith(".csv")]
                if len(filenames) == 0:
                    namelist = ",".join(feed_zip.namelist())
                    self.logger.error(f'missing "{dataset}-*.csv"; ' + f"url={response.url} namelist={namelist}")
                    return
                with feed_zip.open(filenames[0]) as fp:
                    content = fp.read().decode("utf-8").removeprefix("\ufeff")
                    sio = io.StringIO(content)
                    for row in csv.DictReader(sio, delimiter=";"):
                        yield row
        else:
            self.logger.error(f"unexpected Content-Type: {content_type}")
