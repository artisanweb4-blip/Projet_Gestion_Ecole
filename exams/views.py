from rest_framework import viewsets, permissions
from .models import Exam, Question, ExamResult
from .serializers import ExamSerializer, QuestionSerializer, ExamResultSerializer

class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all().order_by('-date')
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['course', 'exam_type']
    search_fields = ['title']

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête (gestionnaire filtrant)
        return Exam.objects.all().order_by('-date')


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('id')
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exam', 'question_type']

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête (gestionnaire filtrant)
        return Question.objects.all().order_by('id')


class ExamResultViewSet(viewsets.ModelViewSet):
    queryset = ExamResult.objects.all().order_by('-created_at')
    serializer_class = ExamResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exam', 'student']

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête (gestionnaire filtrant)
        return ExamResult.objects.all().order_by('-created_at')
