from django import forms
from django.forms import inlineformset_factory

from . import services
from .models import FiberMeasurement, FiberStrand, FiberTest, Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'address', 'client_id', 'logo', 'tolerance_percent']


class FiberTestForm(forms.ModelForm):
    test_datetime = forms.DateTimeField(
        label='Data e ora del test',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    fiber_count = forms.IntegerField(label='Numero di fibre', min_value=1, initial=1)
    selected_wavelengths = forms.MultipleChoiceField(
        label="Lunghezze d'onda da testare",
        choices=services.all_wavelength_choices(),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = FiberTest
        fields = [
            'start_point', 'end_point', 'panel_number', 'fiber_type',
            'length_value', 'length_unit',
            'splice_type', 'splice_count',
            'connector_type', 'connector_count',
            'test_datetime', 'fiber_count', 'selected_wavelengths',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['selected_wavelengths'].initial = [str(wl) for wl in self.instance.selected_wavelengths]

    def clean(self):
        cleaned_data = super().clean()
        fiber_type = cleaned_data.get('fiber_type')
        wavelengths = cleaned_data.get('selected_wavelengths') or []
        if fiber_type:
            valid = {str(wl) for wl in services.wavelengths_for_fiber_type(fiber_type)}
            wavelengths = [wl for wl in wavelengths if wl in valid]
            if not wavelengths:
                self.add_error(
                    'selected_wavelengths',
                    'Seleziona almeno una lunghezza d\'onda valida per il tipo di fibra scelto.',
                )
            cleaned_data['selected_wavelengths'] = [int(wl) for wl in wavelengths]
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.selected_wavelengths = self.cleaned_data['selected_wavelengths']
        if commit:
            instance.save()
        return instance


class FiberStrandForm(forms.ModelForm):
    class Meta:
        model = FiberStrand
        fields = ['panel_position', 'direction_mode']


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
    FiberStrand, FiberMeasurement,
    form=FiberMeasurementForm,
    extra=0,
    can_delete=False,
)
