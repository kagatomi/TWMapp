from django import template
from django.contrib.auth.models import User, Group
from software.models import Task


register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name): 
    group = Group.objects.get(name=group_name) 
    return True if group in user.groups.all() else False


@register.simple_tag
def updateprofile(task, user):
    if task.creator == user:
        if not task in user.profile.viewed_task.all():
            if not user in task.receiver.all():
                user.profile.viewed_task.add(task)
                user.profile.new_task -= 1
            else:            
                user.profile.viewed_task.add(task)
                user.profile.viewed_job.add(task)
                user.profile.new_task -= 1
                user.profile.new_job -= 1
    else:
        if user in task.receiver.all():
            if not task in user.profile.viewed_job.all():
                user.profile.viewed_job.add(task)
                user.profile.new_job -= 1
                
    user.profile.save()
    return ''

@register.simple_tag
def updateprofile_proj(project, user):
    if not project in user.profile.viewed_project.all():
        user.profile.viewed_project.add(project)
        user.profile.new_project -= 1

    user.profile.save()
    return''

@register.simple_tag
def job_view(task, user):
    if not task in user.profile.viewed_job.all():
        return False
    return True


@register.simple_tag
def task_view(task, user):
    if not task in user.profile.viewed_task.all():
        return False
    return True


@register.simple_tag
def project_view(project, user):
    if not project in user.profile.viewed_project.all():
        return False
    return True

@register.simple_tag
def empty_receiver(user):
    grplist = []
    for g in user.groups.all():
        grplist.append(g.name)
    team_task = Task.objects.filter(process__in=grplist).order_by('deadline')
    
    count = 0
    for task in team_task.all():
        list_receivers = ''
        receivers = task.receiver.filter(groups__name__contains=task.process)
        count = len(receivers.all())
        for rcvs in receivers.all():
            list_receivers += str(rcvs.profile)
            if count > 0: list_receivers += ', '
        if list_receivers == '':
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
def is_mytask(task, user):
    grplist = []
    for g in user.groups.all():
        grplist.append(g.name)
    if task.process in grplist :
        return True
    return False
