from locations.hours import DAYS_ES
from locations.spiders.lidl_at import LidlATSpider


class LidlEESpider(LidlATSpider):
    name = "lidl_ee"

    dataset_id = "f3201025df8a4f0084ab28a941fc61a2"
    dataset_name = "Filialdaten-EE/Filialdaten-ee"
    api_key = "AoKxuS8Tx5-VZMhvnRZgacG6XJaANkWzi2fZ49KrJCh72EkdH8qpNfodnH-S-pKq"
    days = DAYS_ES
