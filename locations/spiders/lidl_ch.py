from locations.hours import DAYS_IT
from locations.spiders.lidl_at import LidlATSpider


class LidlCHSpider(LidlATSpider):
    name = "lidl_ch"

    dataset_id = "7d24986af4ad4548bb34f034b067d207"
    dataset_name = "Filialdaten-CH/Filialdaten-CH"
    api_key = "AijRQid01hkLFxKFV7vcRwCWv1oPyY5w6XIWJ-LdxHXxwfH7UUG46Z7dMknbj_rL"
    days = DAYS_IT
