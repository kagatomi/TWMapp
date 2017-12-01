from django.conf.urls import url

from . import views


urlpatterns = [
  url(r'^$', views.index, name='index'),
  url(r'^projects/$', views.ProjectListView.as_view(), name='projects'),
  url(r'^project/(?P<pk>\d+)$', views.ProjectDetailView.as_view(), name='project-detail'),
  url(r'^tasks/$', views.TaskListView.as_view(), name='tasks'),
  url(r'^task/(?P<pk>\d+)$', views.TaskDetailView.as_view(), name='task-detail'),
  url(r'^report/(?P<pk>\d+)$', views.ReportDetailView.as_view(), name='report-detail'),
]


urlpatterns += [   
    url(r'^mytasks/$', views.MyTasksListView.as_view(), name='my-tasks'),
    url(r'^myreports/$', views.MyReportsListView.as_view(), name='my-reports'),
    url(r'^tasked/$', views.TasksAllListView.as_view(), name='all-tasked'),
    url(r'^myteam/$', views.MyTeamView.as_view(), name='my-team'),
]


# Add URLConf to report a task.
urlpatterns += [   
    url(r'^report/create/$', views.ReportCreate.as_view(), name='report_create'),
    url(r'^report/(?P<pk>\d+)/update/$', views.ReportUpdate.as_view(), name='report_update'),
    url(r'^report/(?P<pk>\d+)/delete/$', views.ReportDelete.as_view(), name='report_delete'),
]

# Add URLConf to create, update, and delete projects
urlpatterns += [  
    url(r'^project/create/$', views.ProjectCreate.as_view(), name='project_create'),
    url(r'^project/(?P<pk>\d+)/update/$', views.ProjectUpdate.as_view(), name='project_update'),
    url(r'^project/(?P<pk>\d+)/delete/$', views.ProjectDelete.as_view(), name='project_delete'),
]

urlpatterns += [  
    url(r'^task/create/$', views.TaskCreate.as_view(), name='task_create'),
    url(r'^task/(?P<pk>\d+)/update/$', views.TaskUpdate.as_view(), name='task_update'),
    url(r'^task/(?P<pk>\d+)/delete/$', views.TaskDelete.as_view(), name='task_delete'),
    url(r'^task/(?P<pk>\d+)/edit-receivers/$', views.TaskUpdateReceivers.as_view(), name='task_receivers'),
]

