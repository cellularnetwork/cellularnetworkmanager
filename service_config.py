# service_config.py

def get_service_display_name(service_key):
    # Mappa di esempio per tradurre chiavi tecniche in nomi leggibili
    service_map = {
        'fibra': 'Fibra Ottica',
        'luce': 'Energia Elettrica',
        'gas': 'Gas Naturale',
        'mobile': 'Telefonia Mobile',
        'fisso': 'Telefonia Fissa'
    }
    return service_map.get(service_key, service_key.capitalize())
