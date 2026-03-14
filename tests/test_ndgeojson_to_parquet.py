import shutil
from pathlib import Path

from pandas import read_parquet

from ci.ndgeojsons_to_parquet import to_parquet


def test_to_parquet(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    input_file = Path("./tests/data/dixy_ru.ndgeojson")

    shutil.copy(input_file.absolute(), input_dir.absolute())

    out_dir = tmp_path / "output"
    out_dir.mkdir()
    output_parquet = out_dir / "output.parquet"

    to_parquet(input_dir, output_parquet)

    result_df = read_parquet(output_parquet)

    assert len(result_df) == 4
    columns = result_df.columns.tolist()
    expected_top_level_columns = ["id", "type", "dataset_attributes", "properties", "geom", "bbox"]
    assert all(col in columns for col in expected_top_level_columns)
    # TODO: better GeoParquet file validation
