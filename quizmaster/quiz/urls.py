from django.urls import path, include
from quiz.views import quiz, quizzers, masters

urlpatterns = [
    path('', quiz.home, name='home'),

    path('quizzers/', include(([
        path('', quizzers.QuizListView.as_view(), name='quiz_list'),
        path('interests/', quizzers.QuizzerInterestsView.as_view(), name='quizzer_interests'),
        path('taken/', quizzers.TakenQuizListView.as_view(), name='taken_quiz_list'),
        path('quiz/<int:pk>/', quizzers.take_quiz, name='take_quiz'),
    ], 'quiz'), namespace='quizzers')),

    path('masters/', include(([
        path('', masters.QuizListView.as_view(), name='quiz_change_list'),

        path('quiz/add/', masters.QuizCreateView.as_view(), name='quiz_add'),
        path('quiz/<int:pk>/', masters.QuizUpdateView.as_view(), name='quiz_change'),
        path('quiz/<int:pk>/delete/', masters.QuizDeleteView.as_view(), name='quiz_delete'),
        path('quiz/<int:pk>/results/', masters.QuizResultsView.as_view(), name='quiz_results'),
        path('quiz/<int:pk>/question/add/', masters.question_add, name='question_add'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/', masters.question_change, name='question_change'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/delete/', masters.QuestionDeleteView.as_view(), name='question_delete'),
    ], 'quiz'), namespace='masters')),
]
