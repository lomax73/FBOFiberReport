"""Testi statici del report PDF (IT/EN). L'interfaccia dell'app resta in
italiano: solo il report generato per il cliente viene tradotto, secondo la
lingua scelta sul progetto (Project.report_language)."""

STRINGS = {
    'it': {
        'generated_on': 'Report generato il {date} alle {time}',
        'client': 'Cliente',
        'tolerance': 'Tolleranza di plausibilità: {value}%',
        'topology': 'Topologia rete',
        'fiber_type': 'Tipo fibra',
        'length': 'Lunghezza tratta',
        'test_datetime': 'Data/ora test',
        'splices': 'Giunzioni',
        'connectors': 'Connettori',
        'fiber_count': 'Numero fibre',
        'panel_number': 'N° pannello',
        'fiber': 'Fibra',
        'position': 'posizione',
        'wavelength': 'λ (nm)',
        'direction': 'Direzione',
        'measured': 'Misurato (dB)',
        'theoretical': 'Teorico (dB)',
        'outcome': 'Esito',
        'pending': 'In attesa',
        'verified': 'Verificato',
        'to_verify': 'Da verificare',
        'footer': (
            'Valori teorici stimati con coefficienti tipici (ITU-T G.652/G.657, IEC 60793, prassi '
            'TIA-568): a scopo di verifica di plausibilità, non sostituiscono le specifiche di '
            'capitolato del progetto.'
        ),
    },
    'en': {
        'generated_on': 'Report generated on {date} at {time}',
        'client': 'Client',
        'tolerance': 'Plausibility tolerance: {value}%',
        'topology': 'Network topology',
        'fiber_type': 'Fiber type',
        'length': 'Link length',
        'test_datetime': 'Test date/time',
        'splices': 'Splices',
        'connectors': 'Connectors',
        'fiber_count': 'Fiber count',
        'panel_number': 'Panel no.',
        'fiber': 'Fiber',
        'position': 'position',
        'wavelength': 'λ (nm)',
        'direction': 'Direction',
        'measured': 'Measured (dB)',
        'theoretical': 'Theoretical (dB)',
        'outcome': 'Outcome',
        'pending': 'Pending',
        'verified': 'Verified',
        'to_verify': 'Needs review',
        'footer': (
            'Theoretical values estimated using typical coefficients (ITU-T G.652/G.657, IEC 60793, '
            'TIA-568 practice): for plausibility-check purposes only, they do not replace the project '
            'specifications.'
        ),
    },
}


def strings(lang):
    return STRINGS.get(lang, STRINGS['it'])
