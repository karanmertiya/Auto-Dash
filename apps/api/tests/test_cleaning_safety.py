import pytest

from app.modules.cleaning.safety import UnsafeScriptError, validate_transform_script


def test_allows_single_transform_function() -> None:
    tree = validate_transform_script(
        "def transform(df):\n"
        "    result = df.clone()\n"
        "    return result\n"
    )

    assert tree.body[0].name == "transform"


def test_rejects_imports_and_file_access() -> None:
    with pytest.raises(UnsafeScriptError):
        validate_transform_script("import os\n\ndef transform(df):\n    return df\n")

    with pytest.raises(UnsafeScriptError):
        validate_transform_script("def transform(df):\n    open('secret.txt')\n    return df\n")

