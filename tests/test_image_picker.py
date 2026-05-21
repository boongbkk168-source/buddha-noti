"""Tests for image_picker module."""

import os
from pathlib import Path
from unittest.mock import patch

from src.image_picker import COLOR_KEY, pick


class TestPick:

    def test_all_seven_colors_map_correctly(self):
        for color_th, color_en in COLOR_KEY.items():
            result = pick(color_th, "buddha_day")
            assert Path(result).name in {f"{color_en}_a.png", f"{color_en}_b.png"}

    def test_returns_absolute_png_path(self):
        result = pick("แดง", "buddha_day")
        assert Path(result).is_absolute()
        assert result.endswith(".png")

    def test_random_covers_both_variations(self):
        seen = {Path(pick("แดง", "buddha_day")).name for _ in range(60)}
        assert seen == {"red_a.png", "red_b.png"}

    def test_unknown_color_falls_back_to_yellow(self):
        result = pick("ทอง", "buddha_day")
        assert Path(result).name in {"yellow_a.png", "yellow_b.png"}

    def test_notification_type_does_not_affect_choice(self):
        for ntype in ("buddha_day", "buddha_eve", "kone_eve"):
            result = pick("ฟ้า", ntype)
            assert Path(result).name in {"blue_a.png", "blue_b.png"}

    def test_base_dir_override(self, tmp_path):
        result = pick("แดง", "buddha_day", base_dir=tmp_path)
        assert Path(result).parent == tmp_path.resolve()

    def test_image_override_env(self, tmp_path):
        override = tmp_path / "custom.png"
        override.write_bytes(b"fake")
        with patch.dict(os.environ, {"IMAGE_OVERRIDE": str(override)}):
            result = pick("แดง", "buddha_day")
        assert result == str(override.resolve())

    def test_no_override_uses_color_mapping(self, tmp_path):
        env = {k: v for k, v in os.environ.items() if k != "IMAGE_OVERRIDE"}
        with patch.dict(os.environ, env, clear=True):
            result = pick("ม่วง", "buddha_day", base_dir=tmp_path)
        assert Path(result).name in {"purple_a.png", "purple_b.png"}
