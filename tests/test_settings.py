from easy_cutter.settings import load_settings, save_settings, unique_path


def test_settings_roundtrip(tmp_path):
    path = str(tmp_path / 'sub' / 'settings.json')
    save_settings({'output_dir': 'C:/Clips/Ü'}, path)
    assert load_settings(path) == {'output_dir': 'C:/Clips/Ü'}


def test_missing_or_broken_settings(tmp_path):
    assert load_settings(str(tmp_path / 'fehlt.json')) == {}
    broken = tmp_path / 'kaputt.json'
    broken.write_text('{nicht json', encoding='utf-8')
    assert load_settings(str(broken)) == {}


def test_unique_path(tmp_path):
    path = tmp_path / 'clip.mp4'
    assert unique_path(str(path)) == str(path)
    path.touch()
    second = tmp_path / 'clip_2.mp4'
    assert unique_path(str(path)) == str(second)
    second.touch()
    assert unique_path(str(path)) == str(tmp_path / 'clip_3.mp4')
