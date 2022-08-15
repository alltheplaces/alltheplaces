from locations.commands.insights import CountryUtils


def test_country_fix():
    country_utils = CountryUtils()
    assert not country_utils.to_iso_alpha2_country_code(None)
    assert not country_utils.to_iso_alpha2_country_code("A")
    assert not country_utils.to_iso_alpha2_country_code("A1")
    assert "GB" == country_utils.to_iso_alpha2_country_code("GB")
    assert "GB" == country_utils.to_iso_alpha2_country_code("gb")
    assert "GB" == country_utils.to_iso_alpha2_country_code("Great Britain")
    assert "GB" == country_utils.to_iso_alpha2_country_code("United Kingdom")
    assert "GB" == country_utils.to_iso_alpha2_country_code("United Kingdom. ")
    assert "GB" == country_utils.to_iso_alpha2_country_code("GBR")
    assert "GB" == country_utils.to_iso_alpha2_country_code(" UK ")
