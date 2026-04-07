# Multilingual Support (English & Kiswahili)

This project uses an "Industry Standard" custom localization system that allows for rapid translation without the overhead of complex Django `.po` files.

## 🏗️ Architecture

1.  **Central Catalog**: All UI strings are stored in `members/i18n_strings.py` in two dictionaries: `EXTRA_EN` (English) and `EXTRA_SW` (Swahili).
2.  **Language Manager**: A utility class handles fetching the correct string based on the user's session preference.
3.  **Template Tag**: The `{% church_t 'key' %}` tag is used in HTML templates to display the translated text.
4.  **Language Selector**: A dropdown in the dashboard allows users to switch between languages instantly.

## ➕ How to Add a New String

1.  **Add Key to Dictionary**:
    Open [**i18n_strings.py**](file:///home/mlenda/workstation/church_system/members/i18n_strings.py) and add your new key to both `EXTRA_EN` and `EXTRA_SW`.
    ```python
    # English
    "welcome_message": "Welcome to our Church!",
    
    # Swahili
    "welcome_message": "Karibu katika Kanisa letu!",
    ```

2.  **Use in Template**:
    In your HTML file, load the tag and use the key:
    ```html
    {% load i18n_church %}
    <h1>{% church_t 'welcome_message' %}</h1>
    ```

## 🌍 How to Add a New Language (e.g. French)

1.  **Create New Dictionary**: In `i18n_strings.py`, copy `EXTRA_EN` and rename it to `EXTRA_FR`.
2.  **Update Manager**: In `members/language_utils.py`, add the new language code to the supported list.
3.  **Add to Dropdown**: Update the [**language_selector.html**](file:///home/mlenda/workstation/church_system/members/templates/members/language_selector.html) to include the new language option.

---
*Maintained by the PHM-ARCC Development Team*
