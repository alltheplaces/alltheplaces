from scrapy.http import JsonRequest
from scrapy.spiders import CSVFeedSpider
from scrapy.utils.defer import maybe_deferred_to_future
from twisted.internet.defer import DeferredList

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

# General Bikeshare Feed Specification
# https://gbfs.mobilitydata.org/

# GBFS is a standardized API for operators of bicycles, scooters, moped, and car rental service providers. This
# spider stats at https://github.com/MobilityData/gbfs which offers a centralised catalog of networks or "systems".
# It then processes each system and collects the docks or "stations" from it. Not every system has stations as some
# are dockless.

BRAND_MAPPING = {
    "BA": {"brand": "Bay Wheels", "brand_wikidata": "Q16971391"},
    "bcycle_bublr": {"brand": "Bublr Bikes", "brand_wikidata": "Q108789295"},
    "bcycle_indego": {"brand": "Indego", "brand_wikidata": "Q19876452"},
    "bcycle_memphis": {"brand": "Explore Bike Share", "brand_wikidata": "Q86706492"},
    "bergen-city-bike": {"brand": "Bergen Bysykkel", "brand_wikidata": "Q109288835"},
    "bicimad_madrid": {"brand": "BiciMAD", "brand_wikidata": "Q17402113"},
    "bici_madrid": {"brand": "BiciMAD", "brand_wikidata": "Q17402113"},
    "bike_barcelona": {"brand": "Bicing", "brand_wikidata": "Q1833385"},
    "bike_buenosaires": {"brand": "BA Ecobici", "brand_wikidata": "Q18419538"},
    "bike_share_toronto": {"brand": "Bike Share Toronto", "brand_wikidata": "Q17018523"},
    "biketobike": {"brand": "Mi Bici Tu Bici", "brand_wikidata": "Q100272303"},
    "BIKI_valladolid": {"brand": "Biki", "brand_wikidata": "Q111760142"},
    "bird-bordeaux": {"brand": "Bird"},
    "bird-cascais": {"brand": "Bird"},
    "bird-chalonsenchampagne": {"brand": "Bird"},
    "bird-draguignan": {"brand": "Bird"},
    "bird-larochesuryon": {"brand": "Bird"},
    "bird-laval": {"brand": "Bird"},
    "bird-millau": {"brand": "Bird"},
    "bird-montlucon": {"brand": "Bird"},
    "bird-sarreguemines": {"brand": "Bird"},
    "bird-vichy": {"brand": "Bird"},
    "Bixi_MTL": {"brand": "Bixi", "brand_wikidata": "Q4919302"},
    "bluebike": {"brand": "Blue-bike", "brand_wikidata": "Q17332642"},
    "bluebikes": {"brand": "Bluebikes", "brand_wikidata": "Q3142157"},
    "BoltEU_Brussels": {"brand": "Bolt", "brand_wikidata": "Q20529164"},
    "cabi": {"brand": "Capital Bikeshare", "brand_wikidata": "Q1034635"},
    "callabike": {"brand": "Call a Bike", "brand_wikidata": "Q1060525"},
    "callabike_ice": {"brand": "Call a Bike", "brand_wikidata": "Q1060525"},
    "cc_smartbike_antwerp": {"brand": "Velo", "brand_wikidata": "Q2413118"},
    "cogo": {"brand": "CoGo Bike Share", "brand_wikidata": "Q91342219"},
    "docomo-cycle-tokyo": {"brand": "Docomo Bike Share", "brand_wikidata": "Q55533296"},
    "donkey_aalborg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_aarhus": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_am": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_antwerp": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_ballerup": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_bamberg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_budapest": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_cheltenham_spa": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_cirencester": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_copenhagen": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_den_haag": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_dordrecht": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_frederikshavn": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_ge": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_gh": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_glostrup": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_gorinchem": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_hillerod": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_iisalmi": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_imatra": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kiel": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kingham": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_klampenborg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kotka": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kouvola": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kreuzlingen": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_lappeenranta": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_le_locle": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_li": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_maentsaelae": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_malmoe": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_mikkeli": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_moreton_in_marsh": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_munich": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_neuchatel": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_odense": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_oxford": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_porvoo": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_raasepori": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_regensburg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_reykjavik": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_riihimaki": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_rotterdam_den_haag": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_rt": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_store_heddinge": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_the_cotswold_water_park": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_thun": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_turku": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_ut": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_valenciennes": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_worthing": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_yverdon-les-bains": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "dott-stockholm": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "go_biki": {"brand": "Biki", "brand_wikidata": "Q98337927"},
    "hellocycling": {"brand": "HELLO CYCLING", "brand_wikidata": "Q91231927"},
    "inurba-gdansk": {"brand": "Mevo", "brand_wikidata": "Q60860236"},
    "lyft_dca": {"brand": "Capital Bikeshare", "brand_wikidata": "Q1034635"},
    "MEX": {"brand": "Ecobici", "brand_wikidata": "Q5817067"},
    "netbike_bg": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "neuron_dud": {"brand": "Neuron Mobility"},
    "nextbike_ba": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_bh": {"brand": "MOL Bubi", "brand_wikidata": "Q16971969"},
    "nextbike_bn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_bu": {"brand": "Belfast Bikes", "brand_wikidata": "Q19843240"},
    "nextbike_ch": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_co": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_cq": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_cu": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_cy": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_dd": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_dj": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_dk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_do": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ff": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_gg": {"brand": "OVO Bikes", "brand_wikidata": "Q120450856"},
    "nextbike_hr": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ib": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ka": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_kn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ko": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_la": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_le": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_li": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_lv": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_mz": {"brand": "MVGmeinRad", "brand_wikidata": "Q14541300"},
    "nextbike_na": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nc": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ng": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nh": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nm": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nr": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nt": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nu": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nw": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_pj": {"brand": "SRM Jaskółka", "brand_wikidata": "Q119107871"},
    "nextbike_sl": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_td": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_te": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tf": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tg": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_th": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ti": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tj": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tl": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_to": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tq": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ts": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tt": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tu": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tv": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tx": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ty": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tz": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ud": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uf": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uo": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uv": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_vr": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_wn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_wr": {"brand": "WienMobil Rad", "brand_wikidata": "Q111794110"},
    "nextbike_xa": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_xb": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_xc": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_zz": {"brand": "Metrorower", "brand_wikidata": "Q123507620"},
    "NYC": {"brand": "Citi Bike", "brand_wikidata": "Q2974438"},
    "openvelo_aachen_velocity": {"brand": "Velocity Aachen", "brand_wikidata": "Q102348696"},
    "oslobysykkel": {"brand": "Oslo Bysykkel", "brand_wikidata": "Q7107010"},
    "Paris": {"brand": "Vélib' Metropole", "brand_wikidata": "Q1120762"},
    "peacehealth_rides": {"brand": "PeaceHealth Rides", "brand_wikidata": "Q115393175"},
    "pony_Angers": {"brand": "Pony"},
    "pony_Basque_Country": {"brand": "Pony"},
    "pony_Beauvais": {"brand": "Pony"},
    "pony_Beziers": {"brand": "Pony"},
    "pony_bordeaux": {"brand": "Pony"},
    "pony_Bourges": {"brand": "Pony"},
    "pony_brussels": {"brand": "Pony"},
    "pony_Charleroi": {"brand": "Pony"},
    "pony_Evry": {"brand": "Pony"},
    "pony_Herouville": {"brand": "Pony"},
    "pony_La_Roche_Sur_Yon": {"brand": "Pony"},
    "pony_liège": {"brand": "Pony"},
    "pony_Limoges": {"brand": "Pony"},
    "pony_Lorient": {"brand": "Pony"},
    "pony_Nice": {"brand": "Pony"},
    "pony_Olivet": {"brand": "Pony"},
    "pony_paris": {"brand": "Pony"},
    "pony_Perpignan": {"brand": "Pony"},
    "pony_poitiers": {"brand": "Pony"},
    "publibike": {"brand": "PubliBike", "brand_wikidata": "Q3555363"},
    "regiorad_stuttgart": {"brand": "RegioRad Stuttgart", "brand_wikidata": "Q57274085"},
    "relay_bike_share": {"brand": "Relay Bike Share", "brand_wikidata": "Q48798195"},
    "sharedmobility.ch": {"brand": "Shared Mobility"},
    "stadtrad_hamburg": {"brand": "StadtRAD Hamburg", "brand_wikidata": "Q2326366"},
    "tier_basel": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_bern": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_paris": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_stgallen": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_winterthur": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_zurich": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "velospot_ch": {"brand": "Velospot", "brand_wikidata": "Q56314221"},
    "voi_ch": {"brand": "Voi", "brand_wikidata": "Q61650427"},
    "voi_Marseille": {"brand": "Voi", "brand_wikidata": "Q61650427"},
}

FORM_FACTOR_MAP = {
    "bicycle": {"amenity": "bicycle_rental"},
    "cargo_bicycle": {"amenity": "bicycle_rental", "rental": "cargo_bike"},
    "car": {"amenity": "car_sharing"},
    "moped": {},
    "scooter_standing": {"amenity": "kick-scooter_rental"},
    "scooter_seated": {"amenity": "kick-scooter_rental"},
}

PARKING_TYPE_MAP = {
    "parking_lot": "surface",
    "street_parking": "lane",
    "underground_parking": "underground",
    "sidewalk_parking": "on_kerb",
}


class GbfsSpider(CSVFeedSpider):
    name = "gbfs"
    start_urls = ["https://github.com/MobilityData/gbfs/raw/master/systems.csv"]
    download_delay = 2
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_row(self, response, row):
        yield JsonRequest(url=row["Auto-Discovery URL"], cb_kwargs=row, callback=self.parse_gbfs)

    def set_localized_name(self, item, itemkey, station, stationkey):
        if stationkey not in station:
            return
        value = station[stationkey]
        if isinstance(value, str):
            if itemkey in ("name", "brand", "operator"):
                item[itemkey] = value
            else:
                item["extras"][itemkey] = value
        elif isinstance(value, list):
            for translation in value:
                item["extras"][f"{itemkey}:{translation['language']}"] = translation["text"]
        else:
            self.logger.error(f"Can't handle a localized {stationkey!r} of type {type(value)}")

    def defer_request_feed(self, all_feeds, feed_name, deferreds):
        # List feeds by name.
        feeds = [feed for feed in all_feeds if feed["name"] == feed_name]

        if len(feeds) > 0:
            # If any feeds by that name exist, request the first.
            deferreds.append(self.crawler.engine.download(JsonRequest(url=feeds[0]["url"])))
            return True
        else:
            return False

    def get_next_json(self, has_feed, responses):
        if has_feed:
            success, response = responses.pop(0)
            if success:
                try:
                    return response.json()
                except ValueError as e:
                    self.logger.exception(e)
        return None

    def get_shared_attributes_from_row(self, **kwargs):
        # "network" is a better place than "brand" for the "system name," since a brand can have many non-interoperable networks
        shared_attributes = {"country": kwargs["Country Code"], "extras": {"network": kwargs["Name"]}}

        # TODO: Map all brands/names
        if kwargs["System ID"] in BRAND_MAPPING:
            shared_attributes.update(BRAND_MAPPING[kwargs["System ID"]])
        else:
            # In the absence of a known brand mapping, use the network name.
            shared_attributes["brand"] = kwargs["Name"]

        return shared_attributes

    def update_attributes_from_system_information(self, system_information, shared_attributes):
        system_information = system_information.get("data", system_information)

        self.set_localized_name(shared_attributes, "network", system_information, "name")

        if "opening_hours" in system_information:
            shared_attributes["opening_hours"] = system_information["opening_hours"]

        self.set_localized_name(shared_attributes, "network:short", system_information, "short_name")
        self.set_localized_name(shared_attributes, "operator", system_information, "operator")

    def get_vehicle_types_categories(self, vehicle_types):
        # Map from vehicle_type ID to OSM category
        vehicle_types_categories = {}
        for vehicle_type in DictParser.get_nested_key(vehicle_types, "vehicle_types") or []:
            cat = dict(FORM_FACTOR_MAP.get(vehicle_type["form_factor"], {}))
            if vehicle_type.get("propulsion_type") == "electric_assist":
                if "rental" in cat:
                    cat["rental"] += ";ebike"
                else:
                    cat["rental"] = "ebike"
            vehicle_types_categories[vehicle_type["vehicle_type_id"]] = cat
        return vehicle_types_categories

    def get_station_status_categories(self, station_status, vehicle_types_categories):
        # If a station in station_information doesn't have vechicle_type tags, get it from the station_status feed.
        station_status_categories = {}
        for station in DictParser.get_nested_key(station_status, "stations") or []:
            station_status_categories[station["station_id"]] = [
                vehicle_types_categories.get(vehicle_type["vehicle_type_id"], {})
                for vehicle_type in station.get("vehicle_types_available", [])
            ]
        return station_status_categories

    async def parse_gbfs(self, response, **kwargs):
        try:
            data = response.json()
        except ValueError as e:
            self.logger.exception(e)
            return

        feeds = DictParser.get_nested_key(data, "feeds") or []
        deferreds = []

        # Network and operator information
        has_system_information = self.defer_request_feed(feeds, "system_information", deferreds)

        # Vehicle types, used to determine feature category
        has_vehicle_types = self.defer_request_feed(feeds, "vehicle_types", deferreds)

        # Information about each docking station
        has_station_information = self.defer_request_feed(feeds, "station_information", deferreds)

        # Current status of each docking station.
        # Only needed as fallback if station_information doesn't have vehicle type tags.
        has_station_status = self.defer_request_feed(feeds, "station_status", deferreds)

        if not has_station_information:
            # Can't proceed without station locations.
            self.logger.info(f"{kwargs['Name']}/{kwargs['System ID']} has no station locations")
            return

        # Send off all requests in parallel.
        responses = await maybe_deferred_to_future(DeferredList(deferreds))

        system_information = self.get_next_json(has_system_information, responses)
        vehicle_types = self.get_next_json(has_vehicle_types, responses)
        station_information = self.get_next_json(has_station_information, responses)
        station_status = self.get_next_json(has_station_status, responses)

        # Build a list of attributes common to all stations in this system.
        shared_attributes = self.get_shared_attributes_from_row(**kwargs)

        if isinstance(system_information, dict):
            self.update_attributes_from_system_information(system_information, shared_attributes)

        if vehicle_types is None:
            vehicle_types_categories = {}
        else:
            vehicle_types_categories = self.get_vehicle_types_categories(vehicle_types)

        if station_status is None:
            station_status_categories = {}
        else:
            station_status_categories = self.get_station_status_categories(station_status, vehicle_types_categories)

        # Now scrape the stations.
        for station in DictParser.get_nested_key(station_information, "stations") or []:
            yield self.parse_station(
                station, shared_attributes, vehicle_types_categories, station_status_categories, **kwargs
            )

    def parse_station(self, station, shared_attributes, vehicle_types_categories, station_status_categories, **kwargs):
        item = Feature(**shared_attributes)

        item["ref"] = item["extras"]["ref:gbfs"] = f"{kwargs['System ID']}:{station['station_id']}"
        item["extras"][f"ref:gbfs:{kwargs['System ID']}"] = str(station["station_id"])

        self.set_localized_name(item, "name", station, "name")
        self.set_localized_name(item, "short_name", station, "short_name")

        item["lat"] = station["lat"]
        item["lon"] = station["lon"]

        if "address" in station:
            item["street_address"] = station["address"]

        if "post_code" in station:
            item["postcode"] = station["post_code"]

        if "station_opening_hours" in station:
            item["opening_hours"] = station["station_opening_hours"]

        rental_methods = set(station.get("rental_methods", []))
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "creditcard" in rental_methods)
        apply_yes_no(PaymentMethods.APPLE_PAY, item, "applepay" in rental_methods)
        apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "androidpay" in rental_methods)

        if station.get("is_virtual_station", None) is False:
            # If true, "the station is a location *without* smart docking infrastructure."
            # So, if true or absent, it could be a drop-off location, or a purely virtual station.
            # If false, it must be a docking station.
            item["extras"]["bicycle_rental"] = "docking_station"

        if "station_area" in station:
            item["geometry"] = station["station_area"]

        if "parking_type" in station:
            item["extras"]["parking"] = PARKING_TYPE_MAP.get(station["parking_type"])

        if "contact_phone" in station:
            item["phone"] = station["contact_phone"]

        if "capacity" in station:
            item["extras"]["capacity"] = str(station["capacity"])

        vehicle_types_capacity = station.get("vehicle_types_capacity", [])
        vehicle_docks_capacity = station.get("vehicle_docks_capacity", [])
        total_vehicle_capacity = vehicle_types_capacity + vehicle_docks_capacity
        if len(total_vehicle_capacity) > 0:
            for vehicle_capacity in total_vehicle_capacity:
                for vehicle_type_id in vehicle_capacity["vehicle_type_ids"]:
                    cat = vehicle_types_categories.get(vehicle_type_id, {})
                    apply_category(cat, item)
                    if "rental" in cat and vehicle_capacity.get("count") is not None:
                        for biketype in cat["rental"].split(";"):
                            capacity_key = f"capacity:{biketype}"
                            capacity = item["extras"].get(capacity_key, 0)
                            capacity += vehicle_capacity["count"]
                            item["extras"][capacity_key] = capacity
        elif station["station_id"] in station_status_categories:
            for cat in station_status_categories[station["station_id"]]:
                apply_category(cat, item)

        if station.get("is_charging_station"):
            apply_category(Categories.CHARGING_STATION, item)

        if "rental_uris" in station and "web" in station["rental_uris"]:
            item["website"] = station["rental_uris"]["web"]

        # If neither the vehicle type nor a brand preset were available, set a fallback category.
        if "amenity" not in item["extras"] and not item.get("brand_wikidata"):
            apply_category({"public_transport": "platform"}, item)

        return item
