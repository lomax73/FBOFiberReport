from django.db import migrations

from collaudi import services


def migrate_to_strands(apps, schema_editor):
    FiberTest = apps.get_model('collaudi', 'FiberTest')
    FiberStrand = apps.get_model('collaudi', 'FiberStrand')

    for fiber_test in FiberTest.objects.all():
        strand = FiberStrand.objects.create(fiber_test=fiber_test, number=1)
        measurements = list(fiber_test.measurements_old.all())
        wavelengths = sorted({m.wavelength_nm for m in measurements})
        if not wavelengths:
            wavelengths = services.wavelengths_for_fiber_type(fiber_test.fiber_type)
        fiber_test.selected_wavelengths = wavelengths
        fiber_test.fiber_count = 1
        fiber_test.save()
        for measurement in measurements:
            measurement.strand = strand
            measurement.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('collaudi', '0003_fiberstrand_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_to_strands, noop),
    ]
