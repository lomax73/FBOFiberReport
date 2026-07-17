from decimal import Decimal
from pathlib import Path

from django.db import models
from django.urls import reverse

from . import services


class Project(models.Model):
    name = models.CharField('Nome cantiere', max_length=200)
    address = models.CharField('Indirizzo', max_length=300)
    client_id = models.UUIDField(
        'ID cliente', null=True, blank=True,
        help_text="Riferimento all'anagrafica cliente (quando esisterà).",
    )
    logo = models.ImageField('Logo', upload_to='project_logos/', blank=True)
    tolerance_percent = models.DecimalField(
        'Tolleranza di plausibilità (%)', max_digits=5, decimal_places=2, default=Decimal('15.00'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('project-detail', args=[self.pk])


class FiberTest(models.Model):
    LENGTH_UNIT_CHOICES = [('km', 'km'), ('m', 'm')]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='fiber_tests')
    start_point = models.CharField('Punto di partenza', max_length=200)
    end_point = models.CharField('Punto di arrivo', max_length=200)
    fiber_type = models.CharField('Tipo di fibra', max_length=20, choices=services.fiber_type_choices())
    length_value = models.DecimalField('Lunghezza tratta', max_digits=10, decimal_places=3)
    length_unit = models.CharField('Unità di lunghezza', max_length=2, choices=LENGTH_UNIT_CHOICES, default='km')
    splice_type = models.CharField('Tipo di giunzione', max_length=20, choices=services.splice_type_choices())
    splice_count = models.PositiveIntegerField('Numero giunzioni', default=0)
    connector_type = models.CharField('Tipo di connettori', max_length=20, choices=services.connector_type_choices())
    connector_count = models.PositiveIntegerField('Numero connettori', default=0)
    test_datetime = models.DateTimeField('Data e ora del test')
    fiber_count = models.PositiveIntegerField('Numero di fibre', default=1)
    selected_wavelengths = models.JSONField("Lunghezze d'onda da testare", default=list)
    panel_number = models.CharField('N° pannello', max_length=50, blank=True)

    class Meta:
        ordering = ['start_point', 'end_point']

    def __str__(self):
        return f'{self.start_point} → {self.end_point}'

    @property
    def length_km(self):
        if self.length_unit == 'm':
            return self.length_value / Decimal('1000')
        return self.length_value

    def theoretical_db(self, wavelength_nm):
        return services.theoretical_attenuation_db(self, wavelength_nm)

    def wavelengths(self):
        """Lunghezze d'onda valide per il tipo di fibra (non quelle scelte)."""
        return services.wavelengths_for_fiber_type(self.fiber_type)

    def topology_status(self):
        """Stato aggregato della tratta per il grafo di topologia: 'failed'
        se almeno una misura non è plausibile, 'pending' se nessuna è
        fallita ma qualcuna è ancora senza misura, 'verified' se tutte le
        misure esistenti sono plausibili. Presuppone strands/measurements
        già prefetchate dal chiamante."""
        has_measurement = False
        has_pending = False
        for strand in self.strands.all():
            for measurement in strand.measurements.all():
                has_measurement = True
                if measurement.is_plausible is False:
                    return 'failed'
                if measurement.is_plausible is None:
                    has_pending = True
        if not has_measurement or has_pending:
            return 'pending'
        return 'verified'

    def sync_strands_and_measurements(self):
        """Allinea FiberStrand e FiberMeasurement a fiber_count e
        selected_wavelengths correnti. Da chiamare dopo ogni save da
        form (creazione o modifica tratta)."""
        valid_wavelengths = set(self.wavelengths())
        wavelengths = [wl for wl in self.selected_wavelengths if wl in valid_wavelengths]

        existing_strands = {s.number: s for s in self.strands.all()}
        for number in range(1, self.fiber_count + 1):
            if number not in existing_strands:
                existing_strands[number] = FiberStrand.objects.create(fiber_test=self, number=number)
        for number, strand in list(existing_strands.items()):
            if number > self.fiber_count:
                strand.delete()
                del existing_strands[number]

        for strand in existing_strands.values():
            strand.sync_measurements(wavelengths)


class FiberStrand(models.Model):
    DIRECTION_MODE_CHOICES = [
        ('both', 'Entrambe le direzioni'),
        ('a_to_b', 'Solo A → B'),
        ('b_to_a', 'Solo B → A'),
    ]

    fiber_test = models.ForeignKey(FiberTest, on_delete=models.CASCADE, related_name='strands')
    number = models.PositiveIntegerField('Numero fibra')
    panel_position = models.CharField('Posizione nel pannello', max_length=50, blank=True)
    direction_mode = models.CharField(
        'Direzioni da testare', max_length=10, choices=DIRECTION_MODE_CHOICES, default='both',
    )
    image = models.ImageField('Immagine', upload_to='strand_images/', blank=True)

    class Meta:
        ordering = ['number']
        unique_together = ('fiber_test', 'number')

    def __str__(self):
        return f'{self.fiber_test} · fibra {self.number}'

    @property
    def image_uri(self):
        """URI file:// per l'uso nel report PDF (WeasyPrint), non l'URL
        pubblico servito da Django."""
        if not self.image:
            return None
        return Path(self.image.path).as_uri()

    def directions(self):
        if self.direction_mode == 'a_to_b':
            return ['A_B']
        if self.direction_mode == 'b_to_a':
            return ['B_A']
        return ['A_B', 'B_A']

    def sync_measurements(self, wavelengths):
        """Allinea le FiberMeasurement di questa fibra alle lunghezze d'onda
        e alla direction_mode correnti. Da chiamare dopo ogni save della
        fibra (creazione tratta o modifica impostazioni fibra)."""
        directions = self.directions()
        measurements = self.measurements.all()
        existing_pairs = {(m.wavelength_nm, m.direction) for m in measurements}
        measurements.exclude(wavelength_nm__in=wavelengths).delete()
        measurements.exclude(direction__in=directions).delete()
        for wavelength in wavelengths:
            for direction in directions:
                if (wavelength, direction) not in existing_pairs:
                    FiberMeasurement.objects.create(
                        strand=self, wavelength_nm=wavelength, direction=direction,
                    )


class FiberMeasurement(models.Model):
    DIRECTION_CHOICES = [('A_B', 'A → B'), ('B_A', 'B → A')]

    strand = models.ForeignKey(FiberStrand, on_delete=models.CASCADE, related_name='measurements')
    wavelength_nm = models.PositiveIntegerField('Lunghezza d\'onda (nm)')
    direction = models.CharField('Direzione', max_length=3, choices=DIRECTION_CHOICES)
    measured_db = models.DecimalField(
        'Attenuazione misurata (dB)', max_digits=6, decimal_places=2, null=True, blank=True,
    )

    class Meta:
        ordering = ['wavelength_nm', 'direction']
        constraints = [
            models.UniqueConstraint(
                fields=['strand', 'wavelength_nm', 'direction'],
                name='unique_measurement_per_strand_wavelength_direction',
            ),
        ]

    def __str__(self):
        return f'{self.strand} · {self.wavelength_nm}nm {self.get_direction_display()}'

    @property
    def theoretical_db(self):
        return self.strand.fiber_test.theoretical_db(self.wavelength_nm)

    @property
    def threshold_db(self):
        return services.plausibility_threshold_db(
            self.theoretical_db, self.strand.fiber_test.project.tolerance_percent,
        )

    @property
    def is_plausible(self):
        if self.measured_db is None:
            return None
        return self.measured_db <= self.threshold_db
