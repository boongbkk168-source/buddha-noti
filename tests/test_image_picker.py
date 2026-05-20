"""Tests for image_picker module."""

import os
from pathlib import Path
from unittest.mock import patch

from src.image_picker import pick, COLOR_KEY_MAP, TYPE_KEY


class TestPick:

    def test_returns_existing_path(self, tmp_path):
        result = pick("เหลือง", "buddha_day", base_dir=tmp_path)
        assert Path(result).exists()
        assert result.endswith(".png")

    def test_correct_filename_mapping(self, tmp_path):
        result = pick("แดง", "kone_eve", base_dir=tmp_path)
        assert "red_kone.png" in result

    def test_buddha_eve_uses_buddha_image(self, tmp_path):
        result = pick("ฟ้า", "buddha_eve", base_dir=tmp_path)
        assert "blue_buddha.png" in result

    def test_generates_all_placeholders(self, tmp_path):
        pick("เหลือง", "buddha_day", base_dir=tmp_path)
        expected_count = len(COLOR_KEY_MAP) * len(set(TYPE_KEY.values()))
        png_files = list(tmp_path.glob("*.png"))
        assert len(png_files) == expected_count

    def test_does_not_regenerate_existing(self, tmp_path):
        pick("เหลือง", "buddha_day", base_dir=tmp_path)
        first_mtime = (tmp_path / "yellow_buddha.png").stat().st_mtime
        pick("เหลือง", "buddha_day", base_dir=tmp_path)
        second_mtime = (tmp_path / "yellow_buddha.png").stat().st_mtime
        assert first_mtime == second_mtime

    def test_all_seven_colors(self, tmp_path):
        for color in COLOR_KEY_MAP:
            result = pick(color, "buddha_day", base_dir=tmp_path)
            assert Path(result).exists()

    def test_image_override_env(self, tmp_path):
        override = tmp_path / "custom.png"
        override.write_bytes(b"fake")
        with patch.dict(os.environ, {"IMAGE_OVERRIDE": str(override)}):
            result = pick("แดง", "buddha_day", base_dir=tmp_path)
        assert result == str(override.resolve())

    def test_no_override_uses_normal_mapping(self, tmp_path):
        env = {k: v for k, v in os.environ.items() if k != "IMAGE_OVERRIDE"}
        with patch.dict(os.environ, env, clear=True):
            result = pick("แดง", "buddha_day", base_dir=tmp_path)
        assert "red_buddha.png" in result
