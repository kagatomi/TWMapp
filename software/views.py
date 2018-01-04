from django.shortcuts import render

# Create your views here.
from .models import Profile, Project, Task, Type, TaskProgress
from django.db import models
from django.shortcuts import redirect

from datetime import date, timedelta
from django.utils import timezone
import datetime

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    num_projects = Project.objects.all().count()
    num_tasks = Task.objects.all().count()
    num_projects_new = 0
    num_tasks_new = 0
    for p in Project.objects.all():
        if p.date_of_start + timedelta(days=60) > date.today():
            num_projects_new += 1
    for t in Task.objects.all():
        if t.date_of_init + timedelta(days=7) > timezone.now():
            num_tasks_new += 1
    
    all_projects = Project.objects.all().filter(date_of_start__gt=(date.today()-timedelta(days=60))).order_by('-date_of_start')
    all_tasks = Task.objects.all().filter(receiver=request.user).order_by('-date_of_init')
        
    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_projects':num_projects,
                 'num_tasks':num_tasks,
                 'num_projects_new': num_projects_new,
                 'num_tasks_new':num_tasks_new,
                 'all_tasks':all_tasks,
                 'all_projects':all_projects,},
    )

from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

class ProjectListView(LoginRequiredMixin,generic.ListView):
    model = Project
    paginate_by = 10

class ProjectDetailView(LoginRequiredMixin,generic.DetailView):
    model = Project

class TaskListView(LoginRequiredMixin,generic.ListView):

    model = Task
    paginate_by = 10
    ordering = ['-date_of_init']


class ReportDetailView(LoginRequiredMixin,generic.DetailView):
    model = TaskProgress


class TaskDetailView(LoginRequiredMixin,generic.DetailView):
    model = Task


class MyTasksListView(LoginRequiredMixin,generic.ListView):

    model = Task
    template_name ='software/task_my_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        return Task.objects.filter(
            receiver=self.request.user).order_by('deadline', '-last_update')


class MyReportsListView(LoginRequiredMixin,generic.ListView):
    
    model = TaskProgress
    template_name ='software/taskprogress_my_report.html'
    paginate_by = 10
    
    def get_queryset(self):
        return TaskProgress.objects.filter(reporter=self.request.user).order_by('-date_added')



  
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User, Group

class TasksAllListView(PermissionRequiredMixin,generic.ListView):
    
    model = Task
    permission_required = 'software.is_leader'
    template_name ='software/task_leader_list.html'
    paginate_by = 10

    
    def get_queryset(self):
        grplist = []
        for g in self.request.user.groups.all():
            grplist.append(g.name)
        return Task.objects.filter(process__in=grplist).exclude(status='fi').order_by('deadline')


class MyTeamView(PermissionRequiredMixin,generic.ListView):    
    model = Task
    permission_required = 'software.is_leader'
    template_name ='software/team_job_list.html'
    queryset = Task.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super(MyTeamView, self).get_context_data(**kwargs)
        grplist = []
        for g in self.request.user.groups.all():
            grplist.append(g.name)
        context['team'] = User.objects.filter(groups__name__in=grplist).order_by('first_name')
        for u in User.objects.filter(groups__name__in=grplist).all():
            u.profile.current_task = 0
            u.profile.other_task = 0
            for t in Task.objects.all():
                if u in t.receiver.all() and t.status != 'fi':
                    if t.process in u.profile.grp:
                        u.profile.current_task += 1
                    else:
                        u.profile.other_task += 1
            u.profile.all_task = u.profile.current_task + u.profile.other_task
            u.profile.save()
        return context
    


from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
    
    
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy    


class ProjectCreate(PermissionRequiredMixin, CreateView):
    model = Project
    fields = ['name', 'customer', 'description']
    permission_required = 'software.can_create_project'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.date_of_start = date.today()
        instance.save()

        # Notify new project
        for u in User.objects.all():
            u.profile.unread_project.add(instance)        
            u.profile.save()            
        
        return HttpResponseRedirect(reverse('project-detail', args=[str(instance.pk)]))
    

class ProjectUpdate(PermissionRequiredMixin, UpdateView):
    model = Project
    fields = fields = ['name', 'customer', 'description']
    permission_required = 'software.can_create_project'

    def form_valid(self, form):
        instance = form.save(commit=False)

        # Notify new project
        for u in User.objects.all():
            if not instance in u.profile.unread_project.all():
                u.profile.unread_project.add(instance)
                u.profile.save()

        instance.save()
        return HttpResponseRedirect(reverse('project-detail', args=[str(instance.pk)]))

class ProjectDelete(PermissionRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects')
    permission_required = 'software.can_create_project'

    def delete(self, request, *args, **kwargs):
                
        # Remove notification if a unread project were removed
        project = self.get_object()
        for u in User.objects.all():
            if project in u.profile.unread_project.all():
                u.profile.unread_project.remove(project)
            u.profile.save()

        project.delete()
        return HttpResponseRedirect(reverse('projects') )



import datetime
from .forms import TaskForm

class TaskCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'software.is_member'
    template_name = "software/task_form.html"
    form_class = TaskForm

    def get_form_kwargs(self):
        kwargs = super(TaskCreate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        form.instance.creator = self.request.user
        form.instance.date_of_init = timezone.now()
        instance.save()
        receivers = form.cleaned_data['receivers']
        form.save_m2m()
        for profile in receivers.all():
            instance.receiver.add(profile.user)

        # Add unread task
        for u in instance.receiver.all():
            u.profile.unread_task.add(instance)
            instance.old_receiver.add(u) # Create old receiver
        
        # Add unread task for creator if the person isn't in receiver list
        #if not instance in self.request.user.profile.unread_task.all():
        #    self.request.user.profile.unread_task.add(instance)

        self.request.user.profile.save()
        instance.save()
        return HttpResponseRedirect(reverse('task-detail', args=[str(instance.pk)]))

class TaskUpdate(PermissionRequiredMixin, UpdateView):
    model = Task
    permission_required = 'software.is_member'
    template_name = "software/task_form_update.html"
    form_class = TaskForm

    def get_form_kwargs(self):
        kwargs = super(TaskUpdate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        receivers = form.cleaned_data['receivers']
        form.save_m2m()

        for u in instance.receiver.all():
            instance.receiver.remove(u)
        for profile in receivers.all():
            instance.receiver.add(profile.user)
        instance.save()

        # Add unread task when task updated
        if set(instance.old_receiver.all()) != set(instance.receiver.all()):
            for u in instance.old_receiver.all():
                if instance in u.profile.unread_task.all():
                    u.profile.unread_task.remove(instance)
                    u.profile.save()
                instance.old_receiver.remove(u)
            for u in instance.receiver.all():
                if not instance in u.profile.unread_task.all():
                    u.profile.unread_task.add(instance)                
                instance.old_receiver.add(u)
                u.profile.save()
        else:
            for u in instance.receiver.all():
                if not instance in u.profile.unread_task.all():
                    u.profile.unread_task.add(instance)
                    u.profile.save()

        # Add unread task for creator if the person isn't in receiver list
        # u = instance.creator
        # if not instance in u.profile.unread_task.all():
        #     u.profile.unread_task.add(instance)
        #     u.profile.save()

        instance.save()
        
        return HttpResponseRedirect(reverse('task-detail', args=[str(instance.pk)]))

from .forms import TaskReceiversForm

class TaskUpdateReceivers(PermissionRequiredMixin, UpdateView):
    model = Task
    permission_required = 'software.is_member'
    template_name = "software/task_form.html"
    form_class = TaskReceiversForm

    def get_form_kwargs(self):
        kwargs = super(TaskUpdateReceivers, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save()
        receivers = form.cleaned_data['receivers']
        grp_list = []
        for g in self.request.user.groups.all():
            grp_list.append(g.name)

        team_receiver_list = instance.receiver.filter(groups__name__in=grp_list)
        for u in team_receiver_list.all():
            instance.receiver.remove(u)
        for profile in receivers.all():
            instance.receiver.add(profile.user)
        instance.save()        

        # Add task was updated to unread list for receivers
        if set(instance.old_receiver.all()) != set(instance.receiver.all()):
            for u in instance.old_receiver.all():
                if instance in u.profile.unread_task.all():
                    u.profile.unread_task.remove(instance)
                    u.profile.save()
                    instance.old_receiver.remove(u)
            for u in instance.receiver.all():
                if not instance in u.profile.unread_task.all():
                    u.profile.unread_task.add(instance)
                    instance.old_receiver.add(u)
                u.profile.save()
        else:
            for u in instance.receiver.all():
                if not instance in u.profile.unread_task.all():
                    u.profile.unread_task.add(instance)
                    u.profile.save()

        # Add task was updated to unread list for creator
        # u = instance.creator
        # if not instance in u.profile.unread_task.all():
        #     u.profile.unread_task.add(instance)
        #     u.profile.save()

        instance.save()
        return HttpResponseRedirect(reverse('all_tasked'))

        
class TaskDelete(PermissionRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('tasks')
    permission_required = 'software.is_member'

    def delete(self, request, *args, **kwargs):
        
        # Remove task from unread list 
        task = self.get_object()       
        
        for u in task.receiver.all():
            if task in u.profile.unread_task.all():
                u.profile.unread_task.remove(task)
            u.profile.save()

        # if task in task.creator.profile.unread_task.all():
        #     task.creator.profile.remove(task)
        #     task.creator.profile.save()
            
        task.delete()
        return HttpResponseRedirect(reverse('tasks') )

from .forms import ReportForm

class ReportCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'software.is_member'
    template_name = "software/taskprogress_form.html"
    form_class = ReportForm

    def get_form_kwargs(self):
        kwargs = super(ReportCreate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):  
        instance = form.save(commit=False)
        instance.reporter = self.request.user
        instance.task.status = form.instance.status
        instance.task.process = form.instance.process
        instance.date_added = timezone.now()
        instance.task.last_update = instance.last_update
        
        t = instance.task        

        # Notify for receivers
        for u in t.receiver.all():
            if not t in u.profile.unread_task.all():
                u.profile.unread_task.add(t)
                u.profile.save()

        # Notify for creator
        # u = instance.task.creator
        # if not t in u.profile.unread_task.all():
        #     u.profile.unread_task.add(t)
        #     u.profile.save()
        
        instance.task.save()
        instance.save()
        return HttpResponseRedirect(
            reverse('task-detail', args=[str(form.instance.task.pk)]) )

class ReportUpdate(PermissionRequiredMixin, UpdateView):
    model = TaskProgress
    template_name = "software/taskprogress_form_update.html"
    permission_required = 'software.is_member'
    form_class = ReportForm

    def get_form_kwargs(self):
        kwargs = super(ReportUpdate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.task.status = form.instance.status
        instance.task.process = form.instance.process
        instance.task.last_update = form.instance.last_update
       
        t = instance.task        

        # Notify when report was updated
        for u in t.receiver.all():
            if not t in u.profile.unread_task.all():
                u.profile.unread_task.add(t)
                u.profile.save()

        # u = instance.task.creator
        # if not t in u.profile.unread_task.all():
        #     u.profile.unread_task.add(t)
        #     u.profile.save()

        instance.task.save()
        instance.save()
        return HttpResponseRedirect(
            reverse('task-detail', args=[str(form.instance.task.pk)]) )

class ReportDelete(PermissionRequiredMixin, DeleteView):
    model = TaskProgress
    success_url = reverse_lazy('tasks')
    permission_required = 'software.is_member'

    def delete(self, request, *args, **kwargs):
        
        # Notify if report is removed
        t = self.get_object()            

        for u in t.receiver.all():
            if not t in u.profile.unread_task.all():
                u.profile.unread_task.add(t)
                u.profile.save()

        # if not t in t.creator.profile.unread_task.all():
        #     t.creator.profile.unread_task.add(t)
        #     t.creator.profile.save()
        
        t.delete()
        return HttpResponseRedirect(reverse('my-reports') )
