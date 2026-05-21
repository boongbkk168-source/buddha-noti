"""Tests for image_picker module."""

import os
from pathlib import Path
from unittest.mock import patch

from src.image_picker import VARIATIONS, pick


class TestPick:

    def test_buddha_day_returns_valid_variation(self):
        result = pick("แดง", "buddha_day")
        assert Path(result).name in VARIATIONS["buddha_day"]

    def test_buddha_eve_returns_valid_variation(self):
        result = pick("ฟ้า", "buddha_eve")
        assert Path(result).name in VARIATIONS["buddha_eve"]

    def test_kone_eve_returns_valid_variation(self):
        result = pick("เหลือง", "kone_eve")
        assert Path(result).name in VARIATIONS["kone_eve"]

    def test_returns_absolute_png_path(self):
        result = pick("แดง", "buddha_day")
        assert Path(result).is_absolute()
        assert result.endswith(".png")

    def test_random_covers_both_variations(self):
        seen = {Path(pick("แดง", "buddha_day")).name for _ in range(60)}
        assert seen == set(VARIATIONS["buddha_day"])

    def test_unknown_type_falls_back_to_buddha_day(self):
        result = pick("แดง", "unknown_type")
        assert Path(result).name in VARIATIONS["buddha_day"]

    def test_base_dir_override(self, tmp_path):
        result = pick("แดง", "buddha_day", base_dir=tmp_path)
        assert Path(result).parent == tmp_path.resolve()

    def test_image_override_env(self, tmp_path):
        override = tmp_path / "custom.png"
        override.write_bytes(b"fake")
        with patch.dict(os.environ, {"IMAGE_OVERRIDE": str(override)}):
            result = pick("แดง", "buddha_day")
        assert result == str(override.resolve())

    def test_no_override_uses_variation(self, tmp_path):
        env = {k: v for k, v in os.environ.items() if k != "IMAGE_OVERRIDE"}
        with patch.dict(os.environ, env, clear=True):
            result = pick("แดง", "buddha_day", base_dir=tmp_path)
        assert Path(result).name in VARIATIONS["buddha_day"]
