"""
Configurazione servizi e traduzioni per l'applicazione
"""

SERVICE_TRANSLATIONS = {
    # Vodafone
    'vodafone_sim': 'Vodafone SIM',
    'vodafone_fibra': 'Vodafone Fibra',
    'vodafone_outdoor': 'Vodafone Outdoor',
    'vodafone_indoor': 'Vodafone Indoor',
    'vodafone_business': 'Vodafone Business',
    
    # Wind3
    'wind3_sim': 'Wind3 SIM',
    'wind3_fibra': 'Wind3 Fibra',
    'wind3_outdoor': 'Wind3 Outdoor',
    'wind3_indoor': 'Wind3 Indoor',
    'wind3_business': 'Wind3 Business',
    
    # TIM
    'tim_sim': 'TIM SIM',
    'tim_fibra': 'TIM Fibra',
    'tim_outdoor': 'TIM Outdoor',
    'tim_indoor': 'TIM Indoor',
    'tim_business': 'TIM Business',
    
    # Altri operatori mobile
    'iliad_sim': 'Iliad SIM',
    'iliad_fisso': 'Iliad Fisso',
    'ho_sim': 'ho. SIM',
    'very_mobile_sim': 'Very Mobile SIM',
    'sky_sim': 'Sky SIM',
    'fastweb_sim': 'Fastweb SIM',
    'fastweb_fisso': 'Fastweb Fisso',
    
    # TV e Internet
    'sky_wifi': 'Sky WiFi',
    'sky_tv': 'Sky TV',
    'eolo_fisso': 'Eolo Fisso',
    
    # Energia
    'luce': 'Luce',
    'gas': 'Gas',
    'iren_luce': 'Iren Luce',
    'iren_gas': 'Iren Gas',
    'iren_internet': 'Iren Internet',
    'edison_luce': 'Edison Luce',
    'edison_gas': 'Edison Gas',
    'edison_vas': 'Edison VAS',
    'edison_internet': 'Edison Internet',
    
    # Prodotti Esterni (non inclusi nei target)
    'prodotto_esterno': 'Prodotto Esterno',
    'accessorio': 'Accessorio',
    'telefono': 'Telefono',
    'tablet': 'Tablet',
    'smartwatch': 'Smartwatch',
    'cuffie': 'Cuffie/Auricolari',
    'caricabatterie': 'Caricabatterie',
    'cover_custodia': 'Cover/Custodia',
    'pellicola_protettiva': 'Pellicola Protettiva',
    'powerbank': 'Powerbank',
    'supporti_auto': 'Supporti Auto',
    'altri_accessori': 'Altri Accessori'
}

SERVICE_CATEGORIES = {
    'mobile': [
        'vodafone_sim', 'wind3_sim', 'tim_sim', 'iliad_sim', 
        'ho_sim', 'very_mobile_sim', 'sky_sim', 'fastweb_sim'
    ],
    'fibra': [
        'vodafone_fibra', 'wind3_fibra', 'tim_fibra', 'iliad_fisso',
        'fastweb_fisso', 'sky_wifi', 'eolo_fisso'
    ],
    'outdoor': [
        'vodafone_outdoor', 'wind3_outdoor', 'tim_outdoor'
    ],
    'indoor': [
        'vodafone_indoor', 'wind3_indoor', 'tim_indoor'
    ],
    'business': [
        'vodafone_business', 'wind3_business', 'tim_business'
    ],
    'energia': [
        'luce', 'gas', 'iren_luce', 'iren_gas', 'edison_luce', 
        'edison_gas', 'edison_vas'
    ],
    'internet': [
        'iren_internet', 'edison_internet'
    ],
    'tv': [
        'sky_tv'
    ],
    'prodotti_esterni': [
        'prodotto_esterno', 'accessorio', 'telefono', 'tablet', 'smartwatch',
        'cuffie', 'caricabatterie', 'cover_custodia', 'pellicola_protettiva',
        'powerbank', 'supporti_auto', 'altri_accessori'
    ]
}

SERVICE_ICONS = {
    # Mobile
    'vodafone_sim': 'mobile-alt',
    'wind3_sim': 'mobile-alt',
    'tim_sim': 'mobile-alt',
    'iliad_sim': 'mobile-alt',
    'ho_sim': 'mobile-alt',
    'very_mobile_sim': 'mobile-alt',
    'sky_sim': 'mobile-alt',
    'fastweb_sim': 'mobile-alt',
    
    # Fibra/Internet
    'vodafone_fibra': 'wifi',
    'wind3_fibra': 'wifi',
    'tim_fibra': 'wifi',
    'iliad_fisso': 'wifi',
    'fastweb_fisso': 'wifi',
    'sky_wifi': 'wifi',
    'eolo_fisso': 'wifi',
    'iren_internet': 'wifi',
    'edison_internet': 'wifi',
    
    # Outdoor/Indoor
    'vodafone_outdoor': 'broadcast-tower',
    'wind3_outdoor': 'broadcast-tower',
    'tim_outdoor': 'broadcast-tower',
    'vodafone_indoor': 'home',
    'wind3_indoor': 'home',
    'tim_indoor': 'home',
    
    # Business
    'vodafone_business': 'briefcase',
    'wind3_business': 'briefcase',
    'tim_business': 'briefcase',
    
    # Energia
    'luce': 'bolt',
    'gas': 'fire',
    'iren_luce': 'bolt',
    'iren_gas': 'fire',
    'edison_luce': 'bolt',
    'edison_gas': 'fire',
    'edison_vas': 'plus-circle',
    
    # TV
    'sky_tv': 'tv',
    
    # Prodotti Esterni
    'prodotto_esterno': 'box',
    'accessorio': 'plug',
    'telefono': 'mobile-alt',
    'tablet': 'tablet-alt',
    'smartwatch': 'clock',
    'cuffie': 'headphones',
    'caricabatterie': 'plug',
    'cover_custodia': 'shield-alt',
    'pellicola_protettiva': 'shield-alt',
    'powerbank': 'battery-three-quarters',
    'supporti_auto': 'car',
    'altri_accessori': 'box-open'
}

def get_service_display_name(service_code):
    """Ottieni il nome visualizzato per un servizio"""
    return SERVICE_TRANSLATIONS.get(service_code, service_code.replace('_', ' ').title())

def get_service_icon(service_code):
    """Ottieni l'icona per un servizio"""
    return SERVICE_ICONS.get(service_code, 'circle')

def get_services_by_category():
    """Ottieni servizi raggruppati per categoria"""
    return SERVICE_CATEGORIES