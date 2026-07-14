from decimal import Decimal

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
    length_unit = models.CharField(max_length=2, choices=LENGTH_UNIT_CHOICES, default='km')
    splice_type = models.CharField('Tipo di giunzione', max_length=20, choices=services.splice_type_choices())
    splice_count = models.PositiveIntegerField('Numero giunzioni', default=0)
    connector_type = models.CharField('Tipo di connettori', max_length=20, choices=services.connector_type_choices())
    connector_count = models.PositiveIntegerField('Numero connettori', default=0)
    test_datetime = models.DateTimeField('Data e ora del test')

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
        return services.wavelengths_for_fiber_type(self.fiber_type)


class FiberMeasurement(models.Model):
    DIRECTION_CHOICES = [('A_B', 'A → B'), ('B_A', 'B → A')]

    fiber_test = models.ForeignKey(FiberTest, on_delete=models.CASCADE, related_name='measurements')
    wavelength_nm = models.PositiveIntegerField('Lunghezza d\'onda (nm)')
    direction = models.CharField('Direzione', max_length=3, choices=DIRECTION_CHOICES)
    measured_db = models.DecimalField(
        'Attenuazione misurata (dB)', max_digits=6, decimal_places=2, null=True, blank=True,
    )

    class Meta:
        ordering = ['wavelength_nm', 'direction']
        constraints = [
            models.UniqueConstraint(
                fields=['fiber_test', 'wavelength_nm', 'direction'],
                name='unique_measurement_per_test_wavelength_direction',
            ),
        ]

    def __str__(self):
        return f'{self.fiber_test} · {self.wavelength_nm}nm {self.get_direction_display()}'

    @property
    def theoretical_db(self):
        return self.fiber_test.theoretical_db(self.wavelength_nm)

    @property
    def threshold_db(self):
        return services.plausibility_threshold_db(self.theoretical_db, self.fiber_test.project.tolerance_percent)

    @property
    def is_plausible(self):
        if self.measured_db is None:
            return None
        return self.measured_db <= self.threshold_db
