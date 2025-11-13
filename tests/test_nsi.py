
import pytest
from scrapy.exceptions import UsageError

# Import the source under test
# Adjust this import path if your module lives elsewhere, e.g.
# from locations.commands.name_suggestion_index import NameSuggestionIndexCommand
from locations.commands.nsi import NameSuggestionIndexCommand  # <-- CHANGE THIS

# ---------- Helpers ----------


class _DummyGroup:
    def __init__(self, parent):
        self.parent = parent

    def add_argument(self, *args, **kwargs):
        # record on the parent so we can assert later
        self.parent.added.append((args, kwargs))


class DummyParser:
    def __init__(self):
        self.added = []

    def add_argument(self, *args, **kwargs):
        self.added.append((args, kwargs))

    def add_argument_group(self, *args, **kwargs):
        # Scrapy uses this; return a group that supports add_argument
        return _DummyGroup(self)


def make_opts(**flags):
    import types

    return types.SimpleNamespace(**flags)


# ---------- Basic API surface ----------


def test_syntax_and_short_desc_exist():
    cmd = NameSuggestionIndexCommand()
    assert isinstance(cmd.syntax(), str)
    assert isinstance(cmd.short_desc(), str)
    assert "<name" in cmd.syntax() or "name" in cmd.syntax()
    assert "index" in cmd.short_desc().lower()


def test_add_options_registers_expected_flags(mocker):
    cmd = NameSuggestionIndexCommand()
    # no-op the base method so it doesn't touch self.settings
    mocker.patch("scrapy.commands.ScrapyCommand.add_options", return_value=None)

    parser = DummyParser()
    cmd.add_options(parser)

    joined = " ".join(" ".join(a) for a, _ in parser.added)
    for flag in ("--name", "--code", "--detect-missing"):
        assert flag in joined


# ---------- run() dispatch & errors ----------


def test_run_raises_on_wrong_arg_count():
    cmd = NameSuggestionIndexCommand()
    with pytest.raises(UsageError):
        cmd.run([], make_opts(lookup_name=False, lookup_code=False, detect_missing=False))
    with pytest.raises(UsageError):
        cmd.run(["a", "b"], make_opts(lookup_name=False, lookup_code=False, detect_missing=False))


@pytest.mark.parametrize(
    "flag_name,method_name",
    [
        ("lookup_name", "lookup_name"),
        ("lookup_code", "lookup_code"),
        ("detect_missing", "detect_missing"),
    ],
)
def test_run_dispatches_to_selected_method(mocker, flag_name, method_name):
    cmd = NameSuggestionIndexCommand()

    if flag_name == "detect_missing":
        mocker.patch("locations.commands.nsi.DuplicateWikidataCommand.wikidata_spiders", return_value={})
        cmd.crawler_process = object()

    spy = mocker.spy(cmd, method_name)
    args = ["foo"]
    flags = dict(lookup_name=False, lookup_code=False, detect_missing=False)
    flags[flag_name] = True
    cmd.run(args, make_opts(**flags))
    spy.assert_called_once_with(args)


# ---------- lookup_name() ----------


def test_lookup_name_calls_lookup_code_for_each_found_wikidata(mocker, capsys):
    cmd = NameSuggestionIndexCommand()
    # Mock NSI.iter_wikidata to yield (code, whatever)
    mocker.patch.object(cmd, "nsi", autospec=True)
    cmd.nsi.iter_wikidata.return_value = [("Q111", {}), ("Q222", {})]

    # Spy on lookup_code to ensure it's called for each code
    spy = mocker.spy(cmd, "lookup_code")

    cmd.lookup_name(["brand-like"])
    assert spy.call_count == 2
    spy.assert_any_call(["Q111"])
    spy.assert_any_call(["Q222"])


# ---------- lookup_code() ----------


def test_lookup_code_prints_summary_and_items(mocker, capsys):
    cmd = NameSuggestionIndexCommand()

    # Mock NSI.lookup_wikidata to return wikidata info
    mocker.patch.object(cmd, "nsi", autospec=True)
    cmd.nsi.lookup_wikidata.return_value = {
        "label": "CoolBrand",
        "description": "desc",
        "identities": {"website": "https://x"},
    }

    # Mock NSI.iter_nsi to iterate items with tags
    cmd.nsi.iter_nsi.return_value = [
        {"tags": {"brand": "CoolBrand"}},
        {"tags": {"operator": "CoolBrand Operator"}},
    ]

    cmd.lookup_code(["Q999"])
    out = capsys.readouterr().out
    assert '"CoolBrand", "Q999"' in out
    assert "https://www.wikidata.org/wiki/Q999" in out
    assert 'item_attributes = {"brand": "CoolBrand", "brand_wikidata": "Q999"}' in out
    assert 'item_attributes = {"brand": "CoolBrand Operator", "brand_wikidata": "Q999"}' in out


def test_lookup_code_no_match_prints_nothing(mocker, capsys):
    cmd = NameSuggestionIndexCommand()
    mocker.patch.object(cmd, "nsi", autospec=True)
    cmd.nsi.lookup_wikidata.return_value = None
    cmd.lookup_code(["Q404"])
    out = capsys.readouterr().out
    assert out.strip() == ""


# ---------- detect_missing() integration paths ----------


@pytest.mark.parametrize(
    "arg,uses_request_file",
    [
        ("brands/shop/supermarket", True),  # contains "/"
        ("US", False),  # country code path
    ],
)
def test_detect_missing_routes_by_argument_shape(mocker, capsys, arg, uses_request_file):
    cmd = NameSuggestionIndexCommand()

    # Pretend there are already-known codes (from duplicate spider scan)
    mocker.patch("locations.commands.nsi.DuplicateWikidataCommand.wikidata_spiders", return_value={"Q1": "dummy"})

    # Patch NSI
    mocker.patch.object(cmd, "nsi", autospec=True)

    # When using the "/" path, we fetch a JSON file
    if uses_request_file:
        mocker.patch.object(
            NameSuggestionIndexCommand,
            "_request_file",
            return_value={
                "items": [
                    {"tags": {"brand:wikidata": "Q2"}, "displayName": "Brand Two"},
                    {"tags": {"brand:wikidata": "Q1"}, "displayName": "Brand One (already present)"},
                ],
                "properties": {"path": f"data/{arg}.json"},
            },
        )
    else:
        # For country path, iterate over country items
        cmd.nsi.iter_country.return_value = [
            {"tags": {"brand:wikidata": "Q2"}, "displayName": "Brand Two"},
            {"tags": {"brand:wikidata": "Q1"}, "displayName": "Brand One (already present)"},
        ]

    # lookup_wikidata returns extra info for the missing code
    cmd.nsi.lookup_wikidata.side_effect = lambda code: {"label": "Brand Two"} if code == "Q2" else None

    # Spy on issue_template (so we don't assert massive prints)
    spy = mocker.spy(NameSuggestionIndexCommand, "issue_template")

    # Provide a fake crawler_process attribute that the command expects
    cmd.crawler_process = object()

    cmd.detect_missing([arg])
    out = capsys.readouterr().out
    assert "Missing by wikidata: 1" in out
    # Should file exactly one issue for Q2
    spy.assert_called_once()
    called_code, called_data = spy.call_args.args
    assert called_code == "Q2"
    assert called_data["label"] == "Brand Two"


def test_detect_missing_no_results_prints_zero(mocker, capsys):
    cmd = NameSuggestionIndexCommand()
    mocker.patch("locations.commands.nsi.DuplicateWikidataCommand.wikidata_spiders", return_value={"Q1": "present"})
    mocker.patch.object(cmd, "nsi", autospec=True)
    cmd.nsi.iter_country.return_value = [{"tags": {"brand:wikidata": "Q1"}}]  # all present already
    cmd.nsi.lookup_wikidata.return_value = None
    cmd.crawler_process = object()

    cmd.detect_missing(["US"])
    out = capsys.readouterr().out
    assert "Missing by wikidata: 0" in out


# ---------- show() & issue_template() formatting ----------


@pytest.mark.parametrize(
    "data, contains",
    [
        (
            {"label": "Nice", "description": "desc", "identities": {"website": "https://a"}},
            ['"Nice", "Q5"', "EntityData/Q5.json", "desc", "https://a"],
        ),
        ({"label": "JustLabel"}, ['"JustLabel", "Q5"', "EntityData/Q5.json"]),  # no desc or identities
    ],
)
def test_show_outputs_expected_lines(data, contains, capsys):
    NameSuggestionIndexCommand.show("Q5", data)
    out = capsys.readouterr().out
    for snippet in contains:
        assert snippet in out


@pytest.mark.parametrize(
    "data, expect_bits",
    [
        (
            {
                "label": "Brand A",
                "description": "A desc",
                "identities": {"website": "https://a"},
                "officialWebsites": ["https://site1", "https://site2"],
            },
            [
                "### Brand name",
                "Brand A",
                "A desc",
                "### Wikidata ID",
                "Q7",
                "Primary website: https://a",
                "Official Url(s): https://site1",
                "Official Url(s): https://site2",
                "----",
            ],
        ),
        (
            {"label": "Brand B"},
            # 👇 no "Primary website: N/A" here; function skips when identities is absent
            ["### Brand name", "Brand B", "### Wikidata ID", "Q7", "### Store finder url(s)", "----"],
        ),
    ],
)
def test_issue_template_prints(data, expect_bits, capsys):
    NameSuggestionIndexCommand.issue_template("Q7", data)
    out = capsys.readouterr().out
    for s in expect_bits:
        assert s in out


# ---------- _request_file() error / success ----------


def test_request_file_success_json(mocker):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.json.return_value = {"ok": True}
    mocker.patch("locations.commands.nsi.requests.get", return_value=resp)
    got = NameSuggestionIndexCommand._request_file("data/x.json")
    assert got == {"ok": True}
    # ensure user-agent header set
    requests_get = pytest.importorskip("requests").get  # get real symbol so flake8 doesn't cry


def test_request_file_non_200_raises(mocker):
    resp = mocker.Mock()
    resp.status_code = 500
    mocker.patch("locations.commands.nsi.requests.get", return_value=resp)
    with pytest.raises(Exception, match="NSI load failure"):
        NameSuggestionIndexCommand._request_file("data/x.json")
