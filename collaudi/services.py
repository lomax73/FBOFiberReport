"""
Coefficienti e formula di calcolo dell'attenuazione teorica di tratta,
portati da FIber_util&report/calcolo_attenuazione_fibra.html (stessi
valori usati nel tool HTML di riferimento: ITU-T G.652/G.657, IEC 60793,
prassi TIA-568 — stime di massima, non sostituiscono la misura reale).
"""

from decimal import Decimal

FIBER_TYPES = {
    'sm_g652d': {
        'label': 'Monomodale G.652D',
        'wavelengths': {1310: Decimal('0.35'), 1550: Decimal('0.22'), 1625: Decimal('0.24')},
    },
    'sm_g657': {
        'label': 'Monomodale G.657 A/B',
        'wavelengths': {1310: Decimal('0.35'), 1550: Decimal('0.22'), 1625: Decimal('0.24')},
    },
    'mm_om1': {
        'label': 'Multimodale OM1 (62,5/125)',
        'wavelengths': {850: Decimal('3.5'), 1300: Decimal('1.5')},
    },
    'mm_om2': {
        'label': 'Multimodale OM2 (50/125)',
        'wavelengths': {850: Decimal('3.5'), 1300: Decimal('1.5')},
    },
    'mm_om3': {
        'label': 'Multimodale OM3 (50/125 laser-ott.)',
        'wavelengths': {850: Decimal('3.0'), 1300: Decimal('1.0')},
    },
    'mm_om45': {
        'label': 'Multimodale OM4/OM5 (50/125 laser-ott.)',
        'wavelengths': {850: Decimal('3.0'), 1300: Decimal('1.0')},
    },
}

SPLICE_TYPES = {
    'fusion': {'label': 'Fusione', 'loss': Decimal('0.10')},
    'mechanical': {'label': 'Meccanica', 'loss': Decimal('0.30')},
}

CONNECTOR_TYPES = {
    'factory': {'label': 'Connettorizzato in fabbrica (pigtail)', 'loss': Decimal('0.30')},
    'field': {'label': 'Terminato in campo', 'loss': Decimal('0.50')},
    'generic': {'label': 'Generico / da capitolato', 'loss': Decimal('0.50')},
}


def fiber_type_choices():
    return [(key, val['label']) for key, val in FIBER_TYPES.items()]


def splice_type_choices():
    return [(key, val['label']) for key, val in SPLICE_TYPES.items()]


def connector_type_choices():
    return [(key, val['label']) for key, val in CONNECTOR_TYPES.items()]


def wavelengths_for_fiber_type(fiber_type):
    return sorted(FIBER_TYPES[fiber_type]['wavelengths'].keys())


def default_splice_loss(splice_type):
    return SPLICE_TYPES[splice_type]['loss']


def default_connector_loss(connector_type):
    return CONNECTOR_TYPES[connector_type]['loss']


def theoretical_attenuation_db(fiber_test, wavelength_nm):
    """Attenuazione teorica attesa per una tratta a una data lunghezza d'onda."""
    coeff = FIBER_TYPES[fiber_test.fiber_type]['wavelengths'][wavelength_nm]
    fiber_loss = fiber_test.length_km * coeff
    splice_loss = fiber_test.splice_count * SPLICE_TYPES[fiber_test.splice_type]['loss']
    connector_loss = fiber_test.connector_count * CONNECTOR_TYPES[fiber_test.connector_type]['loss']
    return fiber_loss + splice_loss + connector_loss


def plausibility_threshold_db(theoretical_db, tolerance_percent):
    return theoretical_db * (Decimal('1') + tolerance_percent / Decimal('100'))
