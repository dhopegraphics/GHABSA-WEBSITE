from rest_framework.serializers import Serializer, ModelSerializer
from timetable_system.models import ExaminationSchedule
from academics.serializers import CourseSerializer
from timetable_system.models import ClassSchedule


class ClassScheduleSerializer(ModelSerializer):
    course = CourseSerializer()

    class Meta:
        model = ClassSchedule
        fields = "__all__"


class ExaminationScheduleSerializer(ModelSerializer):
    course = CourseSerializer()

    class Meta:
        model = ExaminationSchedule
        fields = "__all__"
