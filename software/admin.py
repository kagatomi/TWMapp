from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Register your models here.

from .models import Profile, Type, Project, Task, TaskProgress

admin.site.register(Type)

from django.contrib.auth.models import Permission
admin.site.register(Permission)

class ProfileInline(admin.TabularInline):
    model = Profile
    exclude = ['grp']

class CustomUser(UserAdmin):
    inlines = [ProfileInline]

admin.site.unregister(User)    
admin.site.register(User, CustomUser)
admin.site.register(Profile)

@admin.register(TaskProgress)
class TaskProgressAdmin(admin.ModelAdmin):
    list_display = ( 'date_added', 'reporter', 'content', 'status', 'process')

class TaskProgressInline(admin.TabularInline):
    model = TaskProgress
    readonly_fields = ('status', 'date_added')
    exclude = ['content']

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'creator', 'date_of_init', 'deadline')
    list_filter = ('status', 'deadline')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'project', 'creator', 'description', 'date_of_init')
        }),
        ('Informations', {
            'fields': ('status', 'process', 'deadline', 'receiver')
        }),
    )
    inlines = [TaskProgressInline]
    
admin.site.register(Task, TaskAdmin)

class TasksInline(admin.TabularInline):
    model = Task
    readonly_fields = ('title', 'status', 'date_of_init', 'deadline')
    exclude = ['description', 'types']


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer', 'date_of_start')
    exclude = ['tasks']
    inlines = [TasksInline]


admin.site.register(Project, ProjectAdmin)
