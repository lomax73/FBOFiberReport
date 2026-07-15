from pathlib import Path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from weasyprint import HTML

from . import services
from .forms import FiberMeasurementFormSet, FiberStrandForm, FiberTestForm, ProjectForm
from .models import FiberStrand, FiberTest, Project


class CalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'collaudi/calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['coefficients'] = services.coefficients_for_calculator()
        return context


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'collaudi/project_list.html'
    context_object_name = 'projects'


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'collaudi/project_form.html'


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'collaudi/project_form.html'


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'collaudi/project_confirm_delete.html'
    success_url = reverse_lazy('project-list')


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'collaudi/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fiber_tests'] = self.object.fiber_tests.prefetch_related('strands__measurements')
        return context


class FiberTestCreateView(LoginRequiredMixin, CreateView):
    model = FiberTest
    form_class = FiberTestForm
    template_name = 'collaudi/fibertest_form.html'

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs['project_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.get_project()
        context['fiber_type_wavelengths'] = services.fiber_type_wavelength_map()
        return context

    def form_valid(self, form):
        form.instance.project = self.get_project()
        response = super().form_valid(form)
        self.object.sync_strands_and_measurements()
        return response

    def get_success_url(self):
        return reverse('fibertest-measurements', args=[self.object.pk])


class FiberTestUpdateView(LoginRequiredMixin, UpdateView):
    model = FiberTest
    form_class = FiberTestForm
    template_name = 'collaudi/fibertest_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        context['fiber_type_wavelengths'] = services.fiber_type_wavelength_map()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.sync_strands_and_measurements()
        return response

    def get_success_url(self):
        return reverse('project-detail', args=[self.object.project_id])


class FiberTestDeleteView(LoginRequiredMixin, DeleteView):
    model = FiberTest
    template_name = 'collaudi/fibertest_confirm_delete.html'

    def get_success_url(self):
        return reverse('project-detail', args=[self.object.project_id])


def strand_update(request, pk):
    strand = get_object_or_404(FiberStrand, pk=pk)
    fiber_test = strand.fiber_test
    if request.method == 'POST':
        form = FiberStrandForm(request.POST, request.FILES, instance=strand)
        if form.is_valid():
            form.save()
            strand.sync_measurements(fiber_test.selected_wavelengths)
            return redirect('fibertest-measurements', pk=fiber_test.pk)
    else:
        form = FiberStrandForm(instance=strand)
    return render(request, 'collaudi/strand_form.html', {
        'project': fiber_test.project,
        'fiber_test': fiber_test,
        'strand': strand,
        'form': form,
    })


def fibertest_measurements(request, pk):
    fiber_test = get_object_or_404(FiberTest, pk=pk)
    strands = list(fiber_test.strands.prefetch_related('measurements').all())

    if request.method == 'POST':
        formsets = [
            FiberMeasurementFormSet(request.POST, instance=strand, prefix=f'fibra{strand.pk}')
            for strand in strands
        ]
        if all(fs.is_valid() for fs in formsets):
            for fs in formsets:
                fs.save()
            return redirect('project-detail', pk=fiber_test.project_id)
    else:
        formsets = [
            FiberMeasurementFormSet(instance=strand, prefix=f'fibra{strand.pk}')
            for strand in strands
        ]

    strand_groups = [
        {'strand': strand, 'formset': fs, 'rows': list(zip(fs.forms, strand.measurements.all()))}
        for strand, fs in zip(strands, formsets)
    ]
    return render(request, 'collaudi/fibertest_measurements.html', {
        'project': fiber_test.project,
        'fiber_test': fiber_test,
        'strand_groups': strand_groups,
    })


def project_report_pdf(request, pk):
    project = get_object_or_404(Project, pk=pk)
    fiber_tests = project.fiber_tests.prefetch_related('strands__measurements')
    logo_uri = Path(project.logo.path).as_uri() if project.logo else None
    html_string = render_to_string('collaudi/report_pdf.html', {
        'project': project,
        'fiber_tests': fiber_tests,
        'logo_uri': logo_uri,
        'now': timezone.localtime(),
        'request': request,
    })
    pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f'report-{slugify(project.name)}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
