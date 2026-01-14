from django.urls import path

from projects.views.sprint_ai_views import *
from projects.views.sprint_settings_views import *
from .views.projects_views import *
from .views.task_views import *
from .views.comment_view import *
from .views.sprint_views import *
from .views.workflow_views import *
from .views.task_status_history_views import *
from .views.epic_views import *
from projects.views.sprint_planning_views import *
from projects.views.sprint_reports_views import *
from projects.views.sprint_health_views import *
from projects.views.project_teams_view import *
from projects.views.project_file_views import *

urlpatterns = [
    path('add/', ProjectAdd.as_view(), name='project_add'),
    path('list/', ProjectList.as_view(), name='project_list'),
    path('deleted/', DeletedProjectList.as_view(), name='deleted_project_list'),
    path('details/', ProjectDetails.as_view(), name='project_details'),
    path('update/', ProjectUpdate.as_view(), name='project_update'),
    path('summary/', ProjectSummary.as_view(), name='project_update'),
    path('delete/<uuid:project_id>/', ProjectDelete.as_view(), name='project_delete'),
    path('restore/', RestoreProject.as_view(), name='project_restore'),
    path('details/<uuid:id>/', ProjectDetails.as_view(), name='project-details'),

    # --------------------------------------------------
    # Project listings
    # --------------------------------------------------
    path('manager/', ManagerProjects.as_view(), name='manager-projects'),
    path('employee/', EmployeeProjectList.as_view(), name='employee-projects'),
    path('manager/list/', ManagerProjectList.as_view(), name='manager-project-list'),

    # --------------------------------------------------
    # Project configuration
    # --------------------------------------------------
    path('assign-manager/', AssignProjectManager.as_view(), name='assign-project-manager'),

    # --------------------------------------------------
    # Project data views
    # --------------------------------------------------
    path('tasks/', ProjectTasksList.as_view(), name='project-tasks-list'),
    path('milestones/', ProjectMilestonesList.as_view(), name='project-milestones-list'),
    path('users/', ProjectUsers.as_view(), name='project-users'),

    # --------------------------------------------------
    # Project files
    # --------------------------------------------------
 

    # --------------------------------------------------
    # Project finance
    # --------------------------------------------------
    path('invoice/generate/', GenerateProjectInvoice.as_view(), name='generate-project-invoice'),

    # path('abc//', UploadProjectFiles.as_view(), name='upload-files'),
    

   
    path('sprints/list/', SprintList.as_view(), name='sprint_list'),
    path('sprints/details/', SprintDetails.as_view(), name='sprint_details'),
    path('sprints/update/', SprintUpdate.as_view(), name='sprint_update'),
    path('sprints/delete/<uuid:sprint_id>/', SprintDelete.as_view(), name='sprint_delete'),
    
    path('sprints/summary/', SprintSummary.as_view(), name='sprints-summary'),
    
    path('sprints/tasks/', SprintTaskList.as_view()),
    path('task/move/', TaskMove.as_view()),
    # path('tasks/list/', ProjectTasksList.as_view()),
    path('sprints/backlog/', BacklogSimpleList.as_view()),
    path('sprints/start/', SprintStart.as_view()),
    path('sprints/end/', SprintEnd.as_view()),
    path('task/update/properties/', TaskUpdateProperties.as_view()),
    path("sprint/capacity/", SprintCapacityView.as_view()),

    path('sprints/current/', GetCurrentSprint.as_view()), #for empty sprint




    path('task/add/', TaskAdd.as_view(), name='task_add'),
    path('sprints/tasks/', SprintTaskList.as_view(), name='sprint_task_list'),
     path('task/backlog/', BacklogTaskList.as_view(), name='backlog_task_list'),
    path('task/details/', TaskDetails.as_view(), name='task_details'),
    path('task/move/', TaskMove.as_view(), name='task_move'),
    path('task/update/', TaskUpdateDetails.as_view(), name='task-update'),
    path('task/delete/<uuid:task_id>/', TaskDelete.as_view(), name='task_delete'),
    path('task/restore/', RestoreTask.as_view(), name='task_restore'),

    path('comments/add/', CommentAdd.as_view(), name='comment-add'),
    path('comments/list/', CommentList.as_view(), name='comment-list'),
    path('comments/details/', CommentDetails.as_view(), name='comment-details'),
    path('comments/delete/<uuid:comment_id>/', CommentDelete.as_view(), name='comment-delete'),
    path('comments/restore/', RestoreComment.as_view(), name='comment-restore'),



    # --------------------------------------------------
    # Epics
    # --------------------------------------------------
    path('epics/add/', EpicAdd.as_view(), name='epic-add'),

    # --------------------------------------------------
    # Workflow Configuration (OWNER / ADMIN)
    # --------------------------------------------------
    path('workflow/details/', WorkflowDetails.as_view(), name='workflow-details'),
    path('workflow/status/save/', WorkflowStatusUpsert.as_view(), name='workflow-status-upsert'),
    path('workflow/status/delete/<uuid:status_id>/', WorkflowStatusDelete.as_view(), name='workflow-status-delete'),
    path('workflow/transition/save/', WorkflowTransitionUpsert.as_view(), name='workflow-transition-upsert'),
    path('workflow/transition/delete/<uuid:transition_id>/', WorkflowTransitionDelete.as_view(), name='workflow-transition-delete'),


    path('task/status-timeline/', TaskStatusTimeline.as_view(), name='task-status-timeline'),

    # --------------------------------------------------
    # Sprint Planning
    # --------------------------------------------------
    path("sprint/planning/add-task/", AddTaskToSprint.as_view()),
    path("sprint/planning/remove-task/", RemoveTaskFromSprint.as_view()),
    path("sprint/task/bulk-add/", BulkAddTasksToSprint.as_view()),
    path("sprint/ai-plan/", SprintPlanSuggestionView.as_view()),


    # --------------------------------------------------
    # Sprint Reports
    # --------------------------------------------------
    path('sprint/summary/reports/', SprintSummaryReport.as_view()),
    path('sprint/reports/assignees/', SprintAssigneeReport.as_view()),
    path('sprint/reports/spillover/', SprintSpilloverReport.as_view()),
    path('sprints/burndown/', SprintBurndownView.as_view()),
    path('sprints/status-breakdown/', SprintStatusBreakdownReport.as_view()),
    path('sprints/velocity/', SprintVelocityView.as_view()),
    path('sprints/scope-change/', SprintScopeChangeView.as_view()),
    path('sprints/assignee-workload/', SprintAssigneeWorkloadView.as_view()),

    # --------------------------------------------------
    # Sprint Settings
    # --------------------------------------------------

    path("sprint/settings/details/", SprintSettingsDetails.as_view()),
    path("sprint/settings/update/", SprintSettingsUpdate.as_view()),
    path("sprint/settings/start/", SprintStart.as_view()),
    path("sprint/settings/complete/", SprintComplete.as_view()),
    path("sprint/settings/delete/", SprintDelete.as_view()),
    path("sprint/settings/create/", SprintCreate.as_view()),

    # --------------------------------------------------
    # Sprint AI
    # --------------------------------------------------

    path("sprint/ai/explanation/", SprintAIExplanationView.as_view() ),
    path("sprint/ai/trend/", SprintAITrendView.as_view()),

    # Convert AI preview → actual sprint + backlog tasks
    path("sprints/ai/commit/", SprintAICommit.as_view()),
    # Preview sprint tasks from uploaded documents without DB mutation
    path("sprints/ai/preview/", SprintAIPreview.as_view()),

    path("sprints/health/", SprintHealthReport.as_view()),


    # --------------------------------------------------
    # Project Team
    # --------------------------------------------------
    path("team/list/", ProjectTeamList.as_view()),
    path("team/add/", ProjectTeamAdd.as_view()),
    path("team/update-role/", ProjectTeamUpdateRole.as_view()),
    path("team/remove/", ProjectTeamRemove.as_view()),
    path("team/users/list/", UserList.as_view()),


    # projects/urls.py

    path('files/upload', ProjectFileUpload.as_view()),
    path('files/delete', ProjectFileDelete.as_view()),
    path('files/list', ProjectFileList.as_view()),
    path('files/download/<uuid:file_id>/', ProjectFileDownload.as_view(),),


]