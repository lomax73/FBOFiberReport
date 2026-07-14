from django import forms
from django.forms import inlineformset_factory

from .models import FiberMeasurement, FiberTest, Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'address', 'client_id', 'logo', 'tolerance_percent']


class FiberTestForm(forms.ModelForm):
    test_datetime = forms.DateTimeField(
        label='Data e ora del test',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )

    class Meta:
        model = FiberTest
        fields = [
            'start_point', 'end_point', 'fiber_type',
            'length_value', 'length_unit',
            'splice_type', 'splice_count',
            'connector_type', 'connector_count',
            'test_datetime',
        ]


class FiberMeasurementForm(forms.ModelForm):
    measured_db = forms.DecimalField(max_digits=6, decimal_places=2, required=True)

    class Meta:
        model = FiberMeasurement
        fields = ['wavelength_nm', 'direction', 'measured_db']
        widgets = {
            'wavelength_nm': forms.HiddenInput(),
            'direction': forms.HiddenInput(),
        }


FiberMeasurementFormSet = inlineformset_factory(
    FiberTest, FiberMeasurement,
    form=FiberMeasurementForm,
    extra=0,
    can_delete=False,
)
