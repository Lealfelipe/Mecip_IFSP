from django.contrib import admin
from mecip import models

@admin.register(models.Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = 'id', 'campus_name', 'city', 'street', 'neighborhood', 'number', 'email_campus', 'contact_number',
    ordering = '-id',
    search_fields = 'id', 'campus_name', 'city', 'email_campus', 'contact_number',
    list_per_page = 10
    list_max_show_all = 100
    list_display_links = 'id', 'campus_name',

@admin.register(models.Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = 'id', 'type_course', 'description', 'campus',
    ordering = '-id',
    search_fields = 'id', 'type_course', 'description', 'campus',
    list_per_page = 10
    list_max_show_all = 100
    list_display_links = 'id', 'type_course',

    # def campuses(self, obj):
    #     return ", ".join([campus.campus_name for campus in obj.campus.all()])
    # campuses.short_description = 'Campus'

    # list_display += ('campuses',)

@admin.register(models.Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    list_display = 'id', 'course', 'campus',
    ordering = '-id',
    search_fields = 'id', 'course', 'campus',
    list_per_page = 10
    list_max_show_all = 100
    list_display_links = 'id', 'course',

@admin.register(models.Categorie_Course)
class Categorie_Course_Admin(admin.ModelAdmin):
    list_display = 'id', 'categorie',
    ordering = '-id',
    search_fields = 'id', 'categorie',
    list_per_page = 10
    list_max_show_all = 100
    list_display_links = 'id', 'categorie',

@admin.register(models.Type_Course)
class Type_Course_Admin(admin.ModelAdmin):
    list_display = 'id', 'type_name_course', 'duration', 'type_categorie',
    ordering = '-id',
    search_fields = 'id', 'type_name_course', 'type_categorie',
    list_per_page = 10
    list_max_show_all = 100
    list_display_links = 'id', 'type_name_course', 'duration', 'type_categorie',
