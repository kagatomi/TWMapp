from django.db import models
from django.contrib.auth.models import User, Group
import os

# Create your models here.
class Type(models.Model):  
    name = models.CharField(max_length=200,
                            help_text="Enter a request type (e.g. Function, Bug etc.)")
    
    def __str__(self):
        
        return self.name


from django.urls import reverse #Used to generate URLs by reversing the URL patterns



from django.conf import settings
from django.utils import timezone
from datetime import date
import datetime, time
import uuid



class Task(models.Model):    
    title = models.CharField(max_length=200, null=False)
    project = models.ForeignKey('Project',
                                null=False)
    
    description = models.TextField(max_length=2000,
                                   help_text="Enter a description of the task")

    date_of_init = models.DateTimeField(blank=True, null=False)
    last_update = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(blank=False, )
    types = models.ManyToManyField(Type, help_text="Select types of the task")

    creator = models.ForeignKey(User,
                                on_delete=models.SET_NULL,
                                null=True)
    
    receiver = models.ManyToManyField(User, 
                                      related_name="receivers",
                                      null=False)

    old_receiver = models.ManyToManyField(User,
                                          related_name="old_receivers",
                                          null=False)
 
    @property
    def is_outofdate(self):
        if self.status != 'fi':
            if self.deadline and timezone.now() > self.deadline:
                return True
        return False

    @property
    def is_late(self):
        if self.status != 'fi':
            if self.deadline and timezone.now() + datetime.timedelta(days=2) > self.deadline:
                return True
        return False

    
    STATUS = (
        ('n', 'New'),
        ('a', 'Analysising'),
        ('c', 'Coding'),
        ('t', 'Testing'),
        ('f', 'Fixing'),
        ('w', 'Waiting'),
        ('fi', 'Finish'),
    )

    status = models.CharField(max_length=2,
                              choices=STATUS,
                              default='n', 
                              help_text="Choose status for this task. Ex: New, Coding, Finish, etc.")

    PROCESS = (
        ('Analysis', 'Analysis'),
        ('Code', 'Code'),
        ('Test', 'Test'),
    )

    process = models.CharField(max_length=10,
                               choices=PROCESS,
                               default='Analysis', 
                               help_text="Choose the team which is responsibility for this stage. Ex: Analysis for new task or analysising task")
    
    class Meta:
        unique_together = (('title', 'project'))
        ordering = ["deadline"]
        permissions = (("is_manager", "Manager"),
                       ("is_member", "Member"),
                       ("is_leader","Leader"),)

    def get_absolute_url(self):
        return reverse('task-detail', args=[str(self.id)])        

    def __str__(self):
        return '[%s] %s' % (self.project.name,self.title)

    def display_types(self):
        return ', '.join([ types.name for types in self.types.all()[:3] ])
        display_types.short_description = 'Types'


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/report_<id>/<filename>
    timestr = time.strftime("%y%m%d%H%M%S")
    filename = timestr + '_' + filename
    return 'user_{0}/task_{1}/{2}'.format(instance.reporter.id, instance.task.id, filename)


class TaskProgress(models.Model):
    title = models.CharField(max_length=200, null=True)    
    task = models.ForeignKey('Task',
                             null=False)  
    document = models.FileField(blank=True, null=True, upload_to=user_directory_path,
                                help_text="Attach file here.")
    reporter = models.ForeignKey(User,
                                 on_delete=models.SET_NULL,
                                 null=True, blank=False)    
    content = models.TextField(max_length=2000,
                               help_text="Enter content of the report")    
    date_added = models.DateTimeField(blank=True, null=False)
    last_update = models.DateTimeField(auto_now=True)
    
    STATUS = (
        ('n', 'New'),
        ('a', 'Analysising'),
        ('c', 'Coding'),
        ('t', 'Testing'),
        ('f', 'Fixing'),
        ('w', 'Waiting'),
        ('fi', 'Finish'),
    )

    status = models.CharField(max_length=2,
                              choices=STATUS,
                              blank=False,
                              default='n', 
                              help_text="Choose status for this task. Ex: New, Coding, Finish, etc.")

    PROCESS = (
        ('Analysis', 'Analysis'),
        ('Code', 'Code'),
        ('Test', 'Test'),
    )

    process = models.CharField(max_length=10,
                               choices=PROCESS,
                               blank=False,
                               default='Analysis', 
                               help_text="Choose the team which is responsibility for this stage. Ex: Analysis for new task or analysising task")

    
    def get_absolute_url(self):
        return reverse('report-detail', args=[str(self.id)])

    def __str__(self):
        return '%s - (%s)' % (self.task,self.title)




class Project(models.Model):
    
    name = models.CharField(max_length=200)
    customer = models.CharField(max_length=200)  
    description = models.TextField(max_length=2000,
                                   help_text="Enter a description of the project")

    
    date_of_start = models.DateField(blank=True, null=False)
    last_update = models.DateField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    
    def get_absolute_url(self):
        return reverse('project-detail', args=[str(self.id)])

from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    current_task = models.IntegerField(default=0)
    other_task = models.IntegerField(default=0)
    all_task = models.IntegerField(default=0)
    
    unread_task = models.ManyToManyField('Task',
                                         null=True, blank=True,
                                         related_name="unread_task")   
    unread_project = models.ManyToManyField('Project',
                                            null=True, blank=True,
                                            related_name="unread_project") 

    grp = models.CharField(max_length=300, null=True, blank=True)
    
    class Meta:
        ordering = ['grp']

    def __str__(self):
        self.grp = ""
        count = len(self.user.groups.all())
        for g in self.user.groups.all().order_by('name'):
            self.grp += g.name
            count -= 1
            if count > 0: self.grp += ', '
        self.save()
        return '%s %s (%s)' % (self.user.last_name, self.user.first_name, self.grp)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
##    Profile.objects.create(user=instance)
    instance.profile.save()







    
