from django.contrib import admin

from .models import FiberMeasurement, FiberStrand, FiberTest, Project


class FiberMeasurementInline(admin.TabularInline):
    model = FiberMeasurement
    extra = 0


class FiberStrandInline(admin.TabularInline):
    model = FiberStrand
    extra = 0
    show_change_link = True


class FiberTestInline(admin.TabularInline):
    model = FiberTest
    extra = 0
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'tolerance_percent', 'created_at')
    inlines = [FiberTestInline]


@admin.register(FiberTest)
class FiberTestAdmin(admin.ModelAdmin):
    list_display = ('project', 'start_point', 'end_point', 'fiber_type', 'fiber_count', 'test_datetime')
    list_filter = ('project', 'fiber_type')
    inlines = [FiberStrandInline]


@admin.register(FiberStrand)
class FiberStrandAdmin(admin.ModelAdmin):
    list_display = ('fiber_test', 'number')
    inlines = [FiberMeasurementInline]
