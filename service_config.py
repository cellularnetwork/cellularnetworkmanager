# service_config.py

# Mappa dei nomi visualizzati dei servizi
SERVICE_TRANSLATIONS = {
    'fibra': 'Fibra Ottica',
    'luce': 'Energia Elettrica',
    'gas': 'Gas Naturale',
    'mobile': 'Telefonia Mobile',
    'fisso': 'Telefonia Fissa',
    'vodafone_sim': 'Vodafone SIM',
    'vodafone_fibra': 'Vodafone Fibra',
    'wind3_sim': 'WindTre SIM',
    'tim_sim': 'TIM SIM',
    'iliad_sim': 'Iliad SIM',
    'sky_wifi': 'Sky WiFi',
    'edison_luce': 'Edison Luce',
    'edison_gas': 'Edison Gas',
    # aggiungi altri codici qui...
}

# Mappa delle icone (es. per uso frontend con Font Awesome o simili)
SERVICE_ICONS = {
    'fibra': 'wifi',
    'luce': 'bolt',
    'gas': 'fire',
    'mobile': 'mobile',
    'fisso': 'phone',
    'vodafone_sim': 'sim-card',
    'tim_sim': 'sim-card',
    'iliad_sim': 'sim-card',
    # aggiungi altri codici qui...
}

# Categorie di servizi (raggruppamenti opzionali)
SERVICE_CATEGORIES = {
    'Telefonia': ['mobile', 'fisso', 'vodafone_sim', 'tim_sim', 'iliad_sim'],
    'Energia': ['luce', 'gas', 'edison_luce', 'edison_gas'],
    'Internet': ['fibra', 'vodafone_fibra', 'sky_wifi'],
    # aggiungi altre categorie qui...
}

# Funzione fallback (opzionale)
def get_service_display_name(service_key):
    return SERVICE_TRANSLATIONS.get(service_key, service_key.replace('_', ' ').title())
