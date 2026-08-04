import hashlib
import hmac
import json
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signature_key(key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
    k_date = sign(("AWS4" + key).encode("utf-8"), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    return sign(k_service, "aws4_request")


def get_signed_headers(
    method: str,
    url: str,
    payload_bytes: bytes,
    creds: dict,
    region: str = "eu-south-1",
    service: str = "execute-api",
) -> dict:
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"
    query_string = parsed.query or ""

    t = datetime.now(timezone.utc)
    amzdate = t.strftime("%Y%m%dT%H%M%SZ")
    datestamp = t.strftime("%Y%m%d")

    access_key = creds["AccessKeyId"]
    secret_key = creds["SecretKey"]
    session_token = creds["SessionToken"]

    payload_hash = hashlib.sha256(payload_bytes).hexdigest()
    canonical_headers = (
        f"content-type:application/json\nhost:{host}\nx-amz-date:{amzdate}\nx-amz-security-token:{session_token}\n"
    )
    signed_headers = "content-type;host;x-amz-date;x-amz-security-token"
    canonical_request = f"{method}\n{path}\n{query_string}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n{amzdate}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    signing_key = get_signature_key(secret_key, date_stamp=datestamp, region_name=region, service_name=service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    return {
        "content-type": "application/json",
        "x-amz-date": amzdate,
        "x-amz-security-token": session_token,
        "Authorization": f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}",
    }


class PiattaformaUnicaNazionaleITSpider(scrapy.Spider):
    name = "piattaforma_unica_nazionale_it"
    allowed_domains = ["piattaformaunicanazionale.it", "amazonaws.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    IDENTITY_POOL_ID = "eu-south-1:e3b2ab05-2046-43dd-8ed0-c0f14c69d507"
    COGNITO_URL = "https://cognito-identity.eu-south-1.amazonaws.com/"
    API_BASE = "https://api.pun.piattaformaunicanazionale.it"
    PAGE_SIZE = 1000
    GROUP_BATCH_SIZE = 100

    SOCKET_MAP = {
        "IEC_62196_T2": "type2",
        "IEC_62196_T2_COMBO": "type2_combo",
        "CHADEMO": "chademo",
        "IEC_62196_T3A": "type3a",
        "IEC_62196_T3C": "type3c",
        "DOMESTIC_F": "schuko",
        "SCHUKO": "schuko",
        "IEC_60884": "schuko",
        "DOMESTIC_L": "type_l",
        "TESLA": "type2_combo",
    }

    start_urls = ["https://www.piattaformaunicanazionale.it/idr"]
    item_attributes = {"country": "IT"}

    def parse(self, response):
        # Step 1: Obtain Cognito Identity ID
        payload = json.dumps({"IdentityPoolId": self.IDENTITY_POOL_ID})
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityService.GetId",
        }
        yield scrapy.Request(
            url=self.COGNITO_URL,
            method="POST",
            body=payload,
            headers=headers,
            callback=self.parse_cognito_id,
            dont_filter=True,
        )

    def parse_cognito_id(self, response):
        data = response.json()
        identity_id = data.get("IdentityId")
        if not identity_id:
            self.logger.error("Failed to retrieve Cognito Identity ID")
            return

        payload = json.dumps({"IdentityId": identity_id})
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
        }
        yield scrapy.Request(
            url=self.COGNITO_URL,
            method="POST",
            body=payload,
            headers=headers,
            callback=self.parse_cognito_creds,
            dont_filter=True,
        )

    def parse_cognito_creds(self, response):
        creds = response.json().get("Credentials")
        if not creds:
            self.logger.error("Failed to retrieve Cognito Credentials")
            return

        # Start search pagination
        yield from self.fetch_map_page(creds=creds, page=0)

    def fetch_map_page(self, creds: dict, page: int):
        url = f"{self.API_BASE}/v1/chargepoints/public/map/search"
        payload_dict = {"page": page, "size": self.PAGE_SIZE}
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        headers = get_signed_headers("POST", url, payload_bytes, creds)

        yield scrapy.Request(
            url=url,
            method="POST",
            body=payload_bytes,
            headers=headers,
            callback=self.parse_map_search,
            meta={"creds": creds, "page": page},
            dont_filter=True,
        )

    def parse_map_search(self, response):
        data = response.json()
        content = data.get("content", [])
        creds = response.meta["creds"]
        page = response.meta["page"]
        total_pages = data.get("totalPages", 0)

        evse_ids = [item["evse_id"] for item in content if "evse_id" in item]

        # Request details in batches of 100
        for i in range(0, len(evse_ids), self.GROUP_BATCH_SIZE):
            batch = evse_ids[i : i + self.GROUP_BATCH_SIZE]
            url = f"{self.API_BASE}/v1/chargepoints/group"
            payload_bytes = json.dumps(batch).encode("utf-8")
            headers = get_signed_headers("POST", url, payload_bytes, creds)
            yield scrapy.Request(
                url=url,
                method="POST",
                body=payload_bytes,
                headers=headers,
                callback=self.parse_group,
                dont_filter=True,
            )

        # Pagination for next map search page
        if page + 1 < total_pages:
            yield from self.fetch_map_page(creds=creds, page=page + 1)

    def parse_group(self, response):
        items = response.json()
        if not isinstance(items, list):
            return

        # Group EVSEs by locationId to build comprehensive charging stations
        locations = defaultdict(list)
        for evse in items:
            loc_id = evse.get("locationId") or (evse.get("location") or {}).get("_id") or evse.get("evse_id")
            locations[loc_id].append(evse)

        for loc_id, evse_list in locations.items():
            if item := self._parse_station(loc_id, evse_list):
                yield item

    def _parse_station(self, loc_id, evse_list):
        first_evse = evse_list[0]
        loc = first_evse.get("location") or {}
        coords = loc.get("coordinates") or first_evse.get("coordinates") or {}

        lat = coords.get("latitude")
        lon = coords.get("longitude")
        if not lat or not lon:
            return None

        item = Feature()
        item["ref"] = str(loc_id)
        item["lat"] = lat
        item["lon"] = lon

        if address := loc.get("address"):
            item["street_address"] = address.strip()
        if city := loc.get("city"):
            item["city"] = city.strip()
        if state := loc.get("state") or loc.get("region"):
            item["state"] = state.strip()
        if postcode := loc.get("postal_code"):
            item["postcode"] = str(postcode).strip()
        item["country"] = "IT"

        if operator := first_evse.get("businessName"):
            item["operator"] = operator.strip()

        opening_times = loc.get("opening_times") or {}
        if opening_times.get("twentyfourseven") is True:
            item["opening_hours"] = "24/7"

        item["extras"] = self._parse_sockets_and_extras(evse_list)
        apply_category(Categories.CHARGING_STATION, item)
        return item

    def _parse_sockets_and_extras(self, evse_list):
        sockets = defaultdict(list)
        capabilities = set()
        total_connectors = 0
        max_station_power_kw = 0.0

        for evse in evse_list:
            for cap in evse.get("capabilities", []):
                capabilities.add(cap)

            for conn in evse.get("connectors", []):
                total_connectors += 1
                socket_key = self.SOCKET_MAP.get(conn.get("standard"))

                power_w = conn.get("max_electric_power")
                power_kw = None
                if power_w and power_w > 0:
                    power_kw = round(power_w / 1000.0, 1)
                    if power_kw > max_station_power_kw:
                        max_station_power_kw = power_kw

                if socket_key:
                    sockets[socket_key].append(power_kw)

        extras = {}
        for socket_type, powers in sockets.items():
            extras[f"socket:{socket_type}"] = str(len(powers))
            valid_powers = [p for p in powers if p is not None and p > 0]
            if valid_powers:
                max_p = max(valid_powers)
                extras[f"socket:{socket_type}:output"] = f"{int(max_p) if max_p.is_integer() else max_p} kW"

        if total_connectors > 0:
            extras["capacity"] = str(total_connectors)

        if max_station_power_kw > 0:
            out_val = int(max_station_power_kw) if max_station_power_kw.is_integer() else max_station_power_kw
            extras["charging_station:output"] = f"{out_val} kW"

        if "RFID_READER" in capabilities:
            extras["authentication:nfc"] = "yes"
        if "REMOTE_START_STOP_CAPABLE" in capabilities:
            extras["authentication:app"] = "yes"

        return extras
