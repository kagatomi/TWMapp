# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-26 18:51
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_time_login', models.BooleanField(default=True)),
                ('current_task', models.IntegerField(default=0)),
                ('new_job', models.IntegerField(default=0)),
                ('new_task', models.IntegerField(default=0)),
                ('new_project', models.IntegerField(default=0)),
                ('grp', models.CharField(blank=True, max_length=300, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['grp'],
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('customer', models.CharField(max_length=200)),
                ('description', models.TextField(help_text='Enter descriptions of the project', max_length=2000)),
                ('date_of_start', models.DateField(blank=True)),
                ('last_update', models.DateField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(help_text='Enter a description of the task', max_length=2000)),
                ('date_of_init', models.DateTimeField(blank=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('deadline', models.DateTimeField()),
                ('status', models.CharField(choices=[('n', 'New'), ('c', 'Coding'), ('t', 'Testing'), ('f', 'Fixing'), ('fi', 'Finish')], default='n', help_text='New task', max_length=1)),
                ('process', models.CharField(choices=[('Analysis', 'Analysis'), ('Code', 'Change code'), ('Test', 'Test')], default='Analysis', help_text='Analysising', max_length=10)),
                ('creator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('old_receiver', models.ManyToManyField(related_name='old_receivers', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='software.Project')),
                ('receiver', models.ManyToManyField(related_name='receivers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['deadline'],
                'permissions': (('can_create_project', 'Analysis Leader'), ('is_member', 'Member'), ('is_leader', 'Leader')),
            },
        ),
        migrations.CreateModel(
            name='TaskProgress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, null=True)),
                ('content', models.TextField(help_text='Enter content of the report', max_length=2000)),
                ('date_added', models.DateTimeField(blank=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('n', 'New'), ('c', 'Coding'), ('t', 'Testing'), ('f', 'Fixing'), ('fi', 'Finish')], default='n', help_text='New task', max_length=1)),
                ('process', models.CharField(choices=[('Analysis', 'Analysis'), ('Code', 'Change code'), ('Test', 'Test')], default='Analysis', help_text='Analysising', max_length=10)),
                ('reporter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='software.Task')),
            ],
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Enter a request type (e.g. Function, Bug etc.)', max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='types',
            field=models.ManyToManyField(help_text='Select type of the task', to='software.Type'),
        ),
        migrations.AddField(
            model_name='profile',
            name='viewed_job',
            field=models.ManyToManyField(blank=True, null=True, related_name='viewed_job', to='software.Task'),
        ),
        migrations.AddField(
            model_name='profile',
            name='viewed_project',
            field=models.ManyToManyField(blank=True, null=True, related_name='viewed_project', to='software.Project'),
        ),
        migrations.AddField(
            model_name='profile',
            name='viewed_task',
            field=models.ManyToManyField(blank=True, null=True, related_name='viewed_task', to='software.Task'),
        ),
        migrations.AlterUniqueTogether(
            name='task',
            unique_together=set([('title', 'project')]),
        ),
    ]
