from timetable_system.repositories import ExamScheduleRepository, ClassScheduleRepository
from rest_framework import status


def get_exam_schedules_service(request, serializer_classes):
    """
    Get personalized exam schedules for the authenticated user.
    Filters by:
    - User's current year
    - User's current semester
    - Only upcoming exams (future dates only)
    """
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    
    user = request.user
    
    # Get user's year (1, 2, 3, or 4)
    try:
        year = int(user.get_year())
    except (ValueError, AttributeError):
        context = {
            "status": "error",
            "message": "Unable to determine your academic year. Please update your profile.",
            "data": []
        }
        return (bad, context)
    
    # Get user's current semester
    current_semester = user.calculate_current_semester()
    
    # Fetch exam schedules filtered by course year and semester
    exams_repo = ExamScheduleRepository
    exams_qs = exams_repo.get_exam_schedules(year=year, current_semester=current_semester)
    
    # Serialize
    exams = serializer_classes["exams"](exams_qs, many=True)
    
    context = {
        "status": "success",
        "message": f"Exam schedules for Year {year} - Semester {current_semester}",
        "data": exams.data,
        "meta": {
            "year": year,
            "current_semester": current_semester,
            "count": len(exams.data)
        }
    }
    return (ok, context)


def get_class_schedules_service(request, serializer_classes):
    """
    Get personalized class schedules for the authenticated user.
    Filters by:
    - User's current academic year
    - User's program (CS or IT)
    - User's year (1, 2, 3, 4)
    - User's group (G1 or G2) - ONLY for CS students
    - Current semester
    
    Priority: Uses user attributes (personalized approach)
    Fallback: Query params can override if provided
    """
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    
    user = request.user
    repo = ClassScheduleRepository
    
    # Get parameters from query (for admin override) or user profile
    params = request.query_params
    
    # Academic year - use current academic year from user
    academic_year = params.get("academic_year") or user.get_current_academic_year()
    
    # Program - CS or IT
    program = params.get("program") or user.program
    
    # Year - get directly from user (now returns 1, 2, 3, 4)
    try:
        year = int(user.get_year())
    except (ValueError, AttributeError):
        year = params.get("year")
        if year:
            year = int(year)
    
    # Group - G1 or G2 (only required for programs that use groups, like CS)
    group = params.get("group") or user.group
    
    # Current semester
    current_semester = user.calculate_current_semester()
    
    # Validation - check what's required
    missing_fields = []
    if not academic_year:
        missing_fields.append("academic_year")
    if not program:
        missing_fields.append("program")
    if not year:
        missing_fields.append("year")
    
    # Only require group for programs that have groups (currently only CS)
    requires_group = user.requires_group() if program else False
    if requires_group and not group:
        missing_fields.append("group")
    
    if missing_fields:
        context = {
            "status": "error",
            "message": f"Missing required information: {', '.join(missing_fields)}. Please update your profile.",
            "data": [],
            "missing_fields": missing_fields,
            "requires_group_selection": "group" in missing_fields
        }
        return (bad, context)
    
    # Fetch schedules with all filters including semester
    schedules_qs = repo.get_schedules_for_student(
        academic_year=academic_year,
        year=int(year),
        group=group,  # Will be None for IT students, which is fine
        program=program,
        current_semester=current_semester
    )
    
    # Serialize
    serializer = serializer_classes["class_schedules"](schedules_qs, many=True)
    
    # Build message
    group_part = f" {group}" if group else ""
    message = f"Class schedules for {program} Year {year}{group_part} - {academic_year} (Semester {current_semester})"
    
    context = {
        "status": "success",
        "message": message,
        "data": serializer.data,
        "meta": {
            "academic_year": academic_year,
            "program": program,
            "program_display": user.get_program_display_name(),
            "year": year,
            "group": group,
            "group_display": user.get_group_display_name() if group else None,
            "current_semester": current_semester,
            "count": len(serializer.data),
            "requires_group": requires_group
        }
    }
    return (ok, context)


def get_past_exam_schedules_service(request, serializer_classes):
    """
    Get past exam schedules for the authenticated user.
    Filters by:
    - User's current year
    - User's current semester
    - Only past exams (dates before current date/time)
    """
    ok = status.HTTP_200_OK
    bad = status.HTTP_400_BAD_REQUEST
    
    user = request.user
    
    # Get user's year (1, 2, 3, or 4)
    try:
        year = int(user.get_year())
    except (ValueError, AttributeError):
        context = {
            "status": "error",
            "message": "Unable to determine your academic year. Please update your profile.",
            "data": []
        }
        return (bad, context)
    
    # Get user's current semester
    current_semester = user.calculate_current_semester()
    
    # Fetch past exam schedules filtered by course year and semester
    exams_repo = ExamScheduleRepository
    exams_qs = exams_repo.get_past_exam_schedules(year=year, current_semester=current_semester)
    
    # Serialize
    exams = serializer_classes["exams"](exams_qs, many=True)
    
    context = {
        "status": "success",
        "message": f"Past exam schedules for Year {year} - Semester {current_semester}",
        "data": exams.data,
        "meta": {
            "year": year,
            "current_semester": current_semester,
            "count": len(exams.data)
        }
    }
    return (ok, context)


def get_combined_timetable_service(request, serializer_classes):
    """
    Get combined timetable with both class schedules and exam schedules.
    This is the main endpoint for the Timetable page.
    """
    # Get class schedules
    class_status, class_context = get_class_schedules_service(
        request, {"class_schedules": serializer_classes["class_schedules"]}
    )
    
    # Get exam schedules
    exam_status, exam_context = get_exam_schedules_service(
        request, {"exams": serializer_classes["exams"]}
    )
    
    # Combine results
    combined_context = {
        "status": "success",
        "message": "Timetable retrieved successfully",
        "class_schedules": class_context if class_status == status.HTTP_200_OK else {"status": "error", "data": [], "message": class_context.get("message", "")},
        "exam_schedules": exam_context if exam_status == status.HTTP_200_OK else {"status": "error", "data": [], "message": exam_context.get("message", "")},
        "user_info": {
            "year": request.user.get_year(),
            "program": request.user.program,
            "program_display": request.user.get_program_display_name(),
            "group": request.user.group,
            "group_display": request.user.get_group_display_name(),
            "current_semester": request.user.calculate_current_semester(),
            "academic_year": request.user.get_current_academic_year(),
        }
    }
    
    return (status.HTTP_200_OK, combined_context)
