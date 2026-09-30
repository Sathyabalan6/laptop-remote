import pytest
from laptop_remote.core.device import clean_hostname, get_device_display_name, set_custom_device_name


def test_clean_hostname_known_models():
    assert clean_hostname("sathybalan-Vivobook-ASUSLaptop-X1502ZA-X1502ZA", username="sathybalan") == "Vivobook"
    assert clean_hostname("john-macbook-pro", username="john") == "MacBook Pro"
    assert clean_hostname("alice-thinkpad-x1", username="alice") == "ThinkPad"
    assert clean_hostname("bob-dell-xps-13", username="bob") == "XPS"
    assert clean_hostname("carol-surface-pro-9", username="carol") == "Surface Pro"
    assert clean_hostname("dave-galaxy-book-3", username="dave") == "Galaxy Book"
    assert clean_hostname("frank-zenbook-duo", username="frank") == "Zenbook"


def test_clean_hostname_fallbacks():
    assert clean_hostname("DESKTOP-4F8K2L") == "Desktop-4F8K2L"
    assert clean_hostname("LAPTOP-9R8Q21") == "Laptop-9R8Q21"
    assert clean_hostname("ubuntu") == "Ubuntu"
    assert clean_hostname("my-home-server") == "My Home"
    assert clean_hostname("") == "Laptop"


def test_custom_device_name_override(monkeypatch):
    set_custom_device_name("Living Room PC")
    assert get_device_display_name() == "Living Room PC"

    # Explicit override takes precedence
    assert get_device_display_name(custom_name="Den Mac") == "Den Mac"

    set_custom_device_name(None)
