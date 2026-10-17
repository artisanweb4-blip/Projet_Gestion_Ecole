from rest_framework import serializers
from .models import Assignment, AssignmentSubmission
from courses.serializers import CourseSerializer
from students.serializers import StudentSerializer as StudentProfileSerializer

class AssignmentSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Assignment
        fields = ('id', 'title', 'description', 'course', 'course_detail', 'due_date', 'attachment', 'max_score', 'created_at')


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    assignment_detail = AssignmentSerializer(source='assignment', read_only=True)
    student_detail = StudentProfileSerializer(source='student', read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = ('id', 'assignment', 'assignment_detail', 'student', 'student_detail', 'submission_text', 'submitted_file', 'submission_date', 'score', 'feedback', 'created_at')

    def validate(self, attrs):
        instance = AssignmentSubmission(**attrs)
        if self.instance:
            instance.pk = self.instance.pk
        instance.full_clean()
        return attrs
