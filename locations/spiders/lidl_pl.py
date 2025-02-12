from locations.hours import DAYS_PL
from locations.spiders.lidl_at import LidlATSpider


class LidlPLSpider(LidlATSpider):
    name = "lidl_pl"

    dataset_id = "f4c8c3e0d96748348fe904413a798be3"
    dataset_name = "Filialdaten-PL/Filialdaten-PL"
    api_key = "AnZ7UrM33kcHeNxFJsJ6McC4-iAx6Mv55FfsAzmlImV6eJ1n6OX4zfhe2rsut6CD"
    days = DAYS_PL
