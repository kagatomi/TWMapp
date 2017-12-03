from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime #for checking renewal date range.

from django.contrib.auth.models import User, Group
from django import forms
from django.utils import timezone


from .models import Profile, Project, Task, TaskProgress, Type

class TaskForm(forms.ModelForm):   

    class Meta:
        model = Task
        fields = ['title', 'project', 'description',
                    'deadline', 'status', 
                    'process', 'types',]    
        exclude = ['creator', 'receiver',]
        widgets = {
            'deadline': forms.DateTimeInput(
                format='%d-%m-%Y, %H:%M',
                attrs={'class': 'datetime-input ',}),
        }

        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['project'].empty_label = None
        self.fields['status'].empty_label = None
        self.fields['process'].empty_label = None
        task = kwargs.pop('instance')
        grplist = []
        for g in user.groups.all():
            grplist.append(g.name)
##        self.fields['receiver'].queryset = Profile.objects.filter(user__groups__name__in=grplist).values('profile').order_by('user__first_name')
        
        if task is None:
            self.fields['receivers'] = forms.ModelMultipleChoiceField(
                queryset=Profile.objects.filter(
                    user__groups__name__in=grplist).order_by('grp'),
                help_text="Choose the people who are responsibility for this task")
            self.fields['deadline'].initial = timezone.now()
        else:
            self.fields['receivers'] = forms.ModelMultipleChoiceField(
                queryset=Profile.objects.filter(user__groups__name__in=grplist).order_by('grp'),
                initial=(u.profile for u in task.receiver.all()),
                help_text="Choose the people who are responsibility for this task")


class TaskReceiversForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'project', 'description',
                      'deadline', 'status', 'process',
                      'types', ] 
        readonly_fields = ['title', 'project', 'description',
                      'deadline', 'status', 'process',
                      'types', ]    
        exclude = ['creator', 'receiver']
        widgets = {
            'deadline': forms.DateTimeInput(
                format='%d-%m-%Y, %H:%M',
                attrs={'class': 'datetime-input',}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(TaskReceiversForm, self).__init__(*args, **kwargs)
        task = kwargs.pop('instance')
        
        self.fields['title'].disabled = True
        self.fields['project'].disabled = True
        self.fields['description'].disabled = True
        self.fields['deadline'].disabled = True
        self.fields['status'].disabled = True
        self.fields['process'].disabled = True
        self.fields['types'].disabled = True

        grplist = []
        for g in user.groups.all():
            grplist.append(g.name)
        rcvs_list = ""
        for u in task.receiver.all():
            rcvs_list += str(u.profile) +'\n'
        self.fields['current_receivers'] = forms.CharField(
            widget=forms.Textarea(attrs={'readonly': 'readonly'}),
            initial=rcvs_list)

        if task is None:
            self.fields['receivers'] = forms.ModelMultipleChoiceField(
                queryset=Profile.objects.filter(
                    user__groups__name__in=grplist).order_by('grp'),
                help_text="Choose the people who are responsibility for this task")
        else:
            self.fields['receivers'] = forms.ModelMultipleChoiceField(
                queryset=Profile.objects.filter(user__groups__name__in=grplist).order_by('grp'),
                initial=(u.profile for u in task.receiver.all()),
                help_text="Choose the people who are responsibility for this task")


class ReportForm(forms.ModelForm):

    class Meta:
        model = TaskProgress
        fields = ['title', 'task', 'content', 'status', 'process','document' ]
        exclude = ['reporter', ]
        widgets = {
            'document': forms.ClearableFileInput(attrs={'download':True,})
        }

                
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ReportForm, self).__init__(*args, **kwargs)
        report = kwargs.pop('instance')

        self.fields['status'].empty_label = None
        self.fields['process'].empty_label = None        
        self.fields['task'].queryset = Task.objects.filter(receiver=user)
        if report is not None:
            self.fields['task'].disabled = True

