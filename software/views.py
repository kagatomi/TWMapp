from django.shortcuts import render

# Create your views here.
from .models import Profile, Project, Task, Type, TaskProgress
from django.db import models
from django.shortcuts import redirect

from django.contrib.auth.signals import user_logged_in
def check_first_time(sender, user, request, **kwargs):
    
    if request.user.profile.first_time_login:
        request.user.profile.first_time_login = False
        
        for temp in Task.objects.filter(
                receiver=request.user).exclude(
                    status__exact='fi'):
            request.user.profile.new_job += 1

        for temp in Task.objects.filter(
                receiver=request.user, status__exact='fi'):
            request.user.profile.viewed_job.add(temp)

        for temp in Task.objects.filter(creator=request.user):
            request.user.profile.new_task +=1

        for temp in Project.objects.all():
            request.user.profile.viewed_project.add(temp)

        request.user.profile.save()

user_logged_in.connect(check_first_time)

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
        if p.date_of_start + timedelta(days=7) < date.today():
            num_projects_new += 1
    for t in Task.objects.all():
        if t.date_of_init + timedelta(days=1) < timezone.now():
            num_tasks_new += 1
    
    
        
    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_projects':num_projects,
                 'num_tasks':num_tasks,
                 'num_projects_new': num_projects_new,
                 'num_tasks_new':num_tasks_new},
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


class MyJobListsListView(LoginRequiredMixin,generic.ListView):

    model = Task
    template_name ='software/task_my_job_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        return Task.objects.filter(
            receiver=self.request.user).order_by('deadline', '-last_update')

class MyTasksListView(LoginRequiredMixin,generic.ListView):

    model = Task
    template_name ='software/task_my_list_user.html'
    paginate_by = 10
    
    def get_queryset(self):
        return Task.objects.filter(creator=self.request.user).order_by('deadline', '-last_update')

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
        return Task.objects.filter(process__in=grplist).order_by('deadline')


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
            for t in Task.objects.all():
                if u in t.receiver.all():
                    u.profile.current_task += 1
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

        # Notify new project
        for u in User.objects.all():
            u.profile.new_project += 1        
            u.profile.save()
            
        instance.save()
        return HttpResponseRedirect(reverse('projects') )
    

class ProjectUpdate(PermissionRequiredMixin, UpdateView):
    model = Project
    fields = fields = ['name', 'customer', 'description']
    permission_required = 'software.can_create_project'

    def form_valid(self, form):
        instance = form.save(commit=False)

        # Notify new project
        for u in User.objects.all():
            if instance in u.profile.viewed_project.all():
                u.profile.new_project += 1
                u.profile.viewed_project.remove(instance)
                u.profile.save()

        instance.save()
        return HttpResponseRedirect(reverse('projects') )

class ProjectDelete(PermissionRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects')
    permission_required = 'software.can_create_project'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Remove notification if a unread project were removed
        project = self.object.project
        for u in User.objects.all():
            if not project in u.profile.viewed_project.all():
                u.profile.new_project -= 1
            else:
                u.profile.viewed_project.remove(project)
            u.profile.save()
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())



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
        form.instance.date_of_init = datetime.datetime.now()
        instance.save()
        receivers = form.cleaned_data['receivers']
        form.save_m2m()
        for profile in receivers.all():
            instance.receiver.add(profile.user)

        # Notify new task
        self.request.user.profile.new_task += 1
        
        # Notify new job
        for u in form.instance.receiver.all():
            u.profile.new_job += 1
            instance.old_receiver.add(u) # Create old receiver
            
        self.request.user.profile.save()
        instance.save()
        return HttpResponseRedirect(reverse('my-tasks') )

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
        
        # Notify task updated
        u = instance.creator
        if instance in u.profile.viewed_task.all():
            u.profile.new_task += 1
            u.profile.viewed_task.remove(instance)
            u.profile.save()

        # Notify job updated
        if set(instance.old_receiver.all()) != set(instance.receiver.all()):
            for u in instance.old_receiver.all():
                if not instance in u.profile.viewed_job.all():
                    u.profile.new_job -= 1
                    u.profile.save()
                if not u in instance.receiver.all():
                    instance.old_receiver.remove(u)
            for u in instance.receiver.all():
                if instance in u.profile.viewed_job.all():
                    u.profile.viewed_job.remove(form.instance)
                u.profile.new_job +=1
                if not u in instance.old_receiver.all():
                    instance.old_receiver.add(u)
                u.profile.save()
        else:
            for u in instance.receiver.all():
                if instance in u.profile.viewed_job.all():
                    u.profile.viewed_job.remove(instance)
                    u.profile.new_job += 1
                    u.profile.save()
        instance.save()
        
        return HttpResponseRedirect(reverse('my-tasks'))

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

        # Notify task updated
        u = instance.creator
        if instance in u.profile.viewed_task.all():
            u.profile.new_task += 1
            u.profile.viewed_task.remove(instance)
            u.profile.save()

        # Notify job updated
        if set(instance.old_receiver.all()) != set(instance.receiver.all()):
            for u in instance.old_receiver.all():
                if not instance in u.profile.viewed_job.all():
                    u.profile.new_job -= 1
                    u.profile.save()
                if not u in instance.receiver.all():
                    instance.old_receiver.remove(u)
            for u in instance.receiver.all():
                if instance in u.profile.viewed_job.all():
                    u.profile.viewed_job.remove(form.instance)
                u.profile.new_job +=1
                if not u in instance.old_receiver.all():
                    instance.old_receiver.add(u)
                u.profile.save()
        else:
            for u in instance.receiver.all():
                if instance in u.profile.viewed_job.all():
                    u.profile.viewed_job.remove(instance)
                    u.profile.new_job += 1
                    u.profile.save()
        instance.save()
        return HttpResponseRedirect(reverse('task_receivers', args=[str(instance.pk)]))

        
class TaskDelete(PermissionRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('tasks')
    permission_required = 'software.is_member'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Remove notification if unread task ware removed
        task = self.object
        if not task in task.creator.profile.viewed_task.all():
            task.creator.profile.new_task -= 1
        else:
            task.creator.profile.viewed_task.remove(task)
        task.creator.profile.save()
        
        for u in task.receiver.all():
            if not task in u.profile.viewed_job.all():
                u.profile.new_job -= 1
            else:
                u.profile.viewed_job.removed(task)
            u.profile.save()
            
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

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
        instance.date_added = datetime.datetime.now()
        instance.task.last_update = instance.last_update

        # Notify for creator
        u = instance.task.creator
        t = instance.task
        if t in u.profile.viewed_task.all():
            u.profile.new_task += 1
            u.profile.viewed_task.remove(t)
            u.profile.save()

        # Notify for receivers
        for u in t.receiver.all():
            if t in u.profile.viewed_job.all():
                u.profile.viewed_job.remove(t)
                u.profile.new_job += 1
                u.profile.save()
        
        instance.task.save()
        instance.save()
        return HttpResponseRedirect(
            reverse('task-detail', args=[str(form.instance.task.pk)]) )

class ReportUpdate(PermissionRequiredMixin, UpdateView):
    model = TaskProgress
    fields = ['title', 'content', 'status', 'process']
    exclude = ['task', 'reporter']
    template_name = "software/taskprogress_form_update.html"
    permission_required = 'software.is_member'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.task.status = form.instance.status
        instance.task.process = form.instance.process
        instance.task.last_update = form.instance.last_update

        # Notify for creator
        u = instance.task.creator
        t = instance.task
        if t in u.profile.viewed_task.all():
            u.profile.new_task += 1
            u.profile.viewed_task.remove(t)
            u.profile.save()

        # Notify for receivers
        for u in t.receiver.all():
            if t in u.profile.viewed_job.all():
                u.profile.viewed_job.remove(t)
                u.profile.new_job += 1
                u.profile.save()

        instance.task.save()
        instance.save()
        return HttpResponseRedirect(
            reverse('task-detail', args=[str(form.instance.task.pk)]) )

class ReportDelete(PermissionRequiredMixin, DeleteView):
    model = TaskProgress
    success_url = reverse_lazy('tasks')
    permission_required = 'software.is_member'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        #Notify if report ware removed
        t = self.object.task
        if t in t.creator.profile.viewed_task.all():
            t.creator.profile.viewed_task.remove(t)
            t.creator.profile.new_task += 1
            t.creator.profile.save()

        for u in t.receiver.all():
            if t in u.profile.viewed_job.all():
                u.profile.viewed_job.remove(t)
                u.profile.new_job += 1
                u.profile.save()
        
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())
