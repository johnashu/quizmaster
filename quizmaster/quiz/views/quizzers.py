from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

from ..decorators import quizzer_required
from ..forms import QuizzerInterestsForm, QuizzerSignUpForm, TakeQuizForm
from ..models import Quiz, Quizzer, TakenQuiz, User


class QuizzerSignUpView(CreateView):
    model = User
    form_class = QuizzerSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'quizzers'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('quizzers:quiz_list')


@method_decorator([login_required, quizzer_required], name='dispatch')
class QuizzerInterestsView(UpdateView):
    model = Quizzer
    form_class = QuizzerInterestsForm
    template_name = 'quiz/quizzers/interests_form.html'
    success_url = reverse_lazy('quizzers:quiz_list')

    def get_object(self):
        return self.request.user.quizzer

    def form_valid(self, form):
        messages.success(self.request, 'Interests updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, quizzer_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'quiz/quizzers/quiz_list.html'

    def get_queryset(self):
        quizzer = self.request.user.quizzer
        quizzer_interests = quizzer.interests.values_list('pk', flat=True)
        taken_quizzes = quizzer.quizzes.values_list('pk', flat=True)
        queryset = Quiz.objects.filter(topic__in=quizzer_interests) \
            .exclude(pk__in=taken_quizzes) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)
        return queryset


@method_decorator([login_required, quizzer_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'quiz/quizzers/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.quizzer.taken_quizzes \
            .select_related('quiz', 'quiz__topic') \
            .order_by('quiz__name')
        return queryset


@login_required
@quizzer_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quizzer = request.user.quizzer

    if quizzer.quizzes.filter(pk=pk).exists():
        return render(request, 'quizzers/taken_quiz.html')

    total_questions = quiz.questions.count()
    unanswered_questions = quizzer.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                quizzer_answer = form.save(commit=False)
                quizzer_answer.quizzer = quizzer
                quizzer_answer.save()
                if quizzer.get_unanswered_questions(quiz).exists():
                    return redirect('quizzers:take_quiz', pk)
                else:
                    correct_answers = quizzer.quiz_answers.filter(answer__question__quiz=quiz, answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(quizzer=quizzer, quiz=quiz, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (quiz.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the quiz %s with success! You scored %s points.' % (quiz.name, score))
                    return redirect('quizzers:quiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'quiz/quizzers/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })
