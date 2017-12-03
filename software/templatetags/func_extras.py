from django import template
from django.contrib.auth.models import User, Group
from software.models import Task

from datetime import date, timedelta
from django.utils import timezone
import datetime

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name): 
    group = Group.objects.get(name=group_name) 
    return True if group in user.groups.all() else False


@register.simple_tag
def updateprofile(task, user):
    if task in user.profile.unread_task.all():
        user.profile.unread_task.remove(task)
                
    user.profile.save()
    return ''

@register.simple_tag
def updateprofile_proj(project, user):
    if project in user.profile.unread_project.all():
        user.profile.unread_project.remove(project)

    user.profile.save()
    return''


@register.simple_tag
def task_view(task, user):
    if task in user.profile.unread_task.all():
        return False
    return True


@register.simple_tag
def project_view(project, user):
    if project in user.profile.unread_project.all():
        return False
    return True

@register.simple_tag
def empty_receiver(user):
    grplist = []
    for g in user.groups.all():
        grplist.append(g.name)
    team_task = Task.objects.filter(process__in=grplist).exclude(status='fi').order_by('deadline')
    
    count = 0
    for task in team_task.all():
        receivers = task.receiver.filter(groups__name__contains=task.process)
        if len(receivers.all()) == 0:
            count += 1
    
    return count

@register.simple_tag
def number_task_of_project(project):
    count = 0
    for task in Task.objects.all():
        if task.project == project:
            count += 1
    return count

@register.assignment_tag
def receiver_list(task, group):
    list_receivers = ''
    receivers = task.receiver.filter(groups__name__contains=group)
    count = len(receivers.all())
    for rcvs in receivers.all():
        list_receivers += str(rcvs.profile)
        count -= 1
        if count > 0: list_receivers += ', '
    if list_receivers == '':
        return 'Empty'
    else:
        return list_receivers

@register.assignment_tag
def new_project(project):
    if project.date_of_start + timedelta(days=7) > date.today():
        return True
    return False

@register.assignment_tag
def new_task(task):
    if task.date_of_init + timedelta(days=1) > timezone.now():
        return True
    return False

@register.assignment_tag
def is_mytask(task, user):
    grplist = []
    for g in user.groups.all():
        grplist.append(g.name)
    if task.process in grplist :
        return True
    return False

@register.assignment_tag
def number_unread_tasks(user):
    count = len(user.profile.unread_task.all())
    grplist = []
    for g in user.groups.all():
        grplist.append(g.name)
    for task in user.profile.unread_task.all():
        if not task.process in grplist:
            count -= 1
    return count