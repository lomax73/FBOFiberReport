from pathlib import Path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from weasyprint import HTML

from . import services
from .forms import FiberMeasurementFormSet, FiberTestForm, ProjectForm
from .models import FiberMeasurement, FiberTest, Project


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


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'collaudi/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fiber_tests'] = self.object.fiber_tests.prefetch_related('measurements')
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
        return context

    def form_valid(self, form):
        form.instance.project = self.get_project()
        response = super().form_valid(form)
        for wavelength in self.object.wavelengths():
            for direction, _ in FiberMeasurement.DIRECTION_CHOICES:
                FiberMeasurement.objects.create(
                    fiber_test=self.object, wavelength_nm=wavelength, direction=direction,
                )
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
        return context

    def get_success_url(self):
        return reverse('project-detail', args=[self.object.project_id])


def fibertest_measurements(request, pk):
    fiber_test = get_object_or_404(FiberTest, pk=pk)
    if request.method == 'POST':
        formset = FiberMeasurementFormSet(request.POST, instance=fiber_test)
        if formset.is_valid():
            formset.save()
            return redirect('project-detail', pk=fiber_test.project_id)
    else:
        formset = FiberMeasurementFormSet(instance=fiber_test)

    rows = list(zip(formset.forms, fiber_test.measurements.all()))
    return render(request, 'collaudi/fibertest_measurements.html', {
        'project': fiber_test.project,
        'fiber_test': fiber_test,
        'formset': formset,
        'rows': rows,
    })


def project_report_pdf(request, pk):
    project = get_object_or_404(Project, pk=pk)
    fiber_tests = project.fiber_tests.prefetch_related('measurements')
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
