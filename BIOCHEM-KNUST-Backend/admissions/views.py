from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
import hashlib
import time
from .models import (
    AdmissionCriteria, SubjectGradeMapping, AdmissionGuideline,
    EligibilityCheck, FAQ, ImportantDate, WhatsAppHelpdesk, 
    WhatsAppAccessLog, KNUSTAdmission
)
from .serializers import (
    AdmissionCriteriaSerializer, SubjectGradeMappingSerializer,
    AdmissionGuidelineSerializer, EligibilityCheckSerializer,
    EligibilityCheckInputSerializer, FAQSerializer, ImportantDateSerializer,
    WhatsAppHelpdeskSerializer, WhatsAppHelpdeskInputSerializer,
    # Accommodation serializers
    KNUSTAdmissionSerializer, AccommodationVerifySerializer,
    AccommodationNameVerifySerializer, AccommodationUpdateSerializer
)


class AdmissionCriteriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing admission criteria
    """
    queryset = AdmissionCriteria.objects.filter(is_active=True)
    serializer_class = AdmissionCriteriaSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Admission criteria retrieved successfully',
            'data': serializer.data,
            'meta': {
                'total': queryset.count(),
                'programs': ['CS', 'IT']
            }
        })
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current academic year criteria"""
        program = request.query_params.get('program', 'CS')
        criteria = self.queryset.filter(program=program).first()
        
        if not criteria:
            return Response({
                'status': 'error',
                'message': 'No active criteria found for this program'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(criteria)
        return Response({
            'status': 'success',
            'message': 'Current criteria retrieved successfully',
            'data': serializer.data
        })


class SubjectGradeMappingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subject grade mappings
    """
    queryset = SubjectGradeMapping.objects.all()
    serializer_class = SubjectGradeMappingSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Create a grade lookup dictionary
        grade_lookup = {item['grade']: item['numerical_value'] for item in serializer.data}
        
        return Response({
            'status': 'success',
            'message': 'Grade mappings retrieved successfully',
            'data': serializer.data,
            'meta': {
                'grade_lookup': grade_lookup,
                'total_grades': len(grade_lookup)
            }
        })


class AdmissionGuidelineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for admission guidelines
    """
    queryset = AdmissionGuideline.objects.filter(is_active=True)
    serializer_class = AdmissionGuidelineSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        guide_type = request.query_params.get('type', None)
        queryset = self.get_queryset()
        
        if guide_type:
            queryset = queryset.filter(guide_type=guide_type.upper())
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Group by guide type
        grouped_guides = {}
        for guide in serializer.data:
            guide_type_key = guide['guide_type']
            if guide_type_key not in grouped_guides:
                grouped_guides[guide_type_key] = []
            grouped_guides[guide_type_key].append(guide)
        
        return Response({
            'status': 'success',
            'message': 'Guidelines retrieved successfully',
            'data': serializer.data,
            'meta': {
                'grouped': grouped_guides,
                'total': queryset.count()
            }
        })


class EligibilityCheckViewSet(viewsets.ModelViewSet):
    """
    ViewSet for eligibility checks
    """
    queryset = EligibilityCheck.objects.all()
    serializer_class = EligibilityCheckSerializer
    permission_classes = [AllowAny]
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def grade_to_numerical(self, grade):
        """Convert grade to numerical value"""
        try:
            mapping = SubjectGradeMapping.objects.get(grade=grade.upper())
            return mapping.numerical_value
        except SubjectGradeMapping.DoesNotExist:
            return 99  # Fail grade
    
    def check_grade_requirement(self, actual_grade, required_grade):
        """Check if actual grade meets requirement (lower number is better)"""
        actual_num = self.grade_to_numerical(actual_grade)
        required_num = self.grade_to_numerical(required_grade)
        return actual_num <= required_num
    
    def perform_eligibility_check(self, data, request):
        """Perform the actual eligibility check logic"""
        import logging
        logger = logging.getLogger(__name__)
        
        preferred_program = data['preferred_program']
        admission_type = data.get('admission_type', 'REGULAR')
        
        logger.info(f"Checking eligibility for {preferred_program} - {admission_type}")
        
        # Get active criteria for the program
        try:
            criteria = AdmissionCriteria.objects.filter(
                program=preferred_program,
                is_active=True
            ).first()
        except AdmissionCriteria.DoesNotExist:
            return {
                'is_eligible': False,
                'meets_regular': False,
                'meets_feepaying': False,
                'admission_type': admission_type,
                'details': {},
                'recommendations': 'No active criteria found for this program.'
            }
        
        if not criteria:
            return {
                'is_eligible': False,
                'meets_regular': False,
                'meets_feepaying': False,
                'admission_type': admission_type,
                'details': {},
                'recommendations': 'No active criteria available. Please contact admissions.'
            }
        
        # Initialize results
        results = {
            'aggregate_check': False,
            'aggregate_calculation': {
                'total': data['aggregate_score'],
                'core_used': [],  # Will store the 3 core subjects used
                'electives_used': []  # Will store the 3 electives used
            },
            'core_subjects': {},
            'elective_subjects': {},
            'overall_pass': False,
            'criteria_used': {
                'program': criteria.get_program_display(),
                'academic_year': criteria.academic_year,
                'aggregate_cutoff': criteria.aggregate_cutoff
            }
        }
        
        recommendations = []
        
        # Document which subjects were used in aggregate calculation
        # Best 3 core: English, Math, and best of (Science or Social)
        science_num = self.grade_to_numerical(data['integrated_science_grade'])
        social_num = self.grade_to_numerical(data['social_studies_grade'])
        best_third_core = 'integrated_science' if science_num <= social_num else 'social_studies'
        
        results['aggregate_calculation']['core_used'] = [
            {'subject': 'Core Mathematics', 'grade': data['core_math_grade'], 'points': self.grade_to_numerical(data['core_math_grade'])},
            {'subject': 'English Language', 'grade': data['english_grade'], 'points': self.grade_to_numerical(data['english_grade'])},
            {'subject': 'Integrated Science' if best_third_core == 'integrated_science' else 'Social Studies', 
             'grade': data[f'{best_third_core}_grade'], 
             'points': min(science_num, social_num)}
        ]
        
        # Best 3 electives
        elective_list = []
        for field, name in [
            ('elective_math_grade', 'Elective Mathematics'),
            ('physics_grade', 'Physics'),
            ('chemistry_grade', 'Chemistry'),
            ('biology_grade', 'Biology'),
            ('elective_ict_grade', 'Elective ICT'),
            ('other_elective_1_grade', data.get('other_elective_1', 'Other Elective 1')),
            ('other_elective_2_grade', data.get('other_elective_2', 'Other Elective 2'))
        ]:
            if data.get(field):
                elective_list.append({
                    'subject': name,
                    'grade': data[field],
                    'points': self.grade_to_numerical(data[field])
                })
        
        elective_list.sort(key=lambda x: x['points'])  # Sort by points (best first)
        results['aggregate_calculation']['electives_used'] = elective_list[:3]
        
        # Check aggregate score
        aggregate_score = data['aggregate_score']
        if aggregate_score <= criteria.aggregate_cutoff:
            results['aggregate_check'] = True
        else:
            recommendations.append(
                f"Your aggregate ({aggregate_score}) exceeds the cutoff ({criteria.aggregate_cutoff}). "
                f"Lower aggregate is better. You need {aggregate_score - criteria.aggregate_cutoff} points to improve."
            )
        
        # Check core subjects
        core_checks = {
            'core_math': {
                'actual': data['core_math_grade'],
                'required': criteria.core_math_min_grade,
                'passed': self.check_grade_requirement(data['core_math_grade'], criteria.core_math_min_grade),
                'subject_name': 'Core Mathematics'
            },
            'english': {
                'actual': data['english_grade'],
                'required': criteria.english_min_grade,
                'passed': self.check_grade_requirement(data['english_grade'], criteria.english_min_grade),
                'subject_name': 'English Language'
            },
            'integrated_science': {
                'actual': data['integrated_science_grade'],
                'required': criteria.integrated_science_min_grade,
                'passed': self.check_grade_requirement(data['integrated_science_grade'], criteria.integrated_science_min_grade),
                'subject_name': 'Integrated Science'
            },
            'social_studies': {
                'actual': data['social_studies_grade'],
                'required': criteria.social_studies_min_grade,
                'passed': self.check_grade_requirement(data['social_studies_grade'], criteria.social_studies_min_grade),
                'subject_name': 'Social Studies'
            }
        }
        
        results['core_subjects'] = core_checks
        
        # Add recommendations for failed core subjects
        for key, check in core_checks.items():
            if not check['passed']:
                recommendations.append(
                    f"{check['subject_name']}: You have {check['actual']}, but need at least {check['required']}"
                )
        
        # Check elective subjects
        elective_checks = {}
        
        # Elective Mathematics
        if criteria.elective_math_required:
            if data.get('elective_math_grade'):
                passed = self.check_grade_requirement(
                    data['elective_math_grade'],
                    criteria.elective_math_min_grade
                )
                elective_checks['elective_math'] = {
                    'actual': data['elective_math_grade'],
                    'required': criteria.elective_math_min_grade,
                    'passed': passed,
                    'subject_name': 'Elective Mathematics',
                    'is_required': True
                }
                if not passed:
                    recommendations.append(
                        f"Elective Mathematics: You have {data['elective_math_grade']}, "
                        f"but need at least {criteria.elective_math_min_grade}"
                    )
            else:
                elective_checks['elective_math'] = {
                    'actual': 'Not provided',
                    'required': criteria.elective_math_min_grade,
                    'passed': False,
                    'subject_name': 'Elective Mathematics',
                    'is_required': True
                }
                recommendations.append("Elective Mathematics is required but not provided")
        
        # Physics
        if criteria.physics_required:
            if data.get('physics_grade'):
                passed = self.check_grade_requirement(
                    data['physics_grade'],
                    criteria.physics_min_grade
                )
                elective_checks['physics'] = {
                    'actual': data['physics_grade'],
                    'required': criteria.physics_min_grade,
                    'passed': passed,
                    'subject_name': 'Physics',
                    'is_required': True
                }
                if not passed:
                    recommendations.append(
                        f"Physics: You have {data['physics_grade']}, "
                        f"but need at least {criteria.physics_min_grade}"
                    )
            else:
                elective_checks['physics'] = {
                    'actual': 'Not provided',
                    'required': criteria.physics_min_grade,
                    'passed': False,
                    'subject_name': 'Physics',
                    'is_required': True
                }
                recommendations.append("Physics is required but not provided")
        
        # Count science electives (including physics, chemistry, biology, ICT)
        science_electives = []
        
        # Include physics in science electives count
        if data.get('physics_grade'):
            science_electives.append('physics')
            if 'physics' not in elective_checks:
                elective_checks['physics'] = {
                    'actual': data['physics_grade'],
                    'passed': True,
                    'subject_name': 'Physics'
                }
        
        # Count other science subjects
        for subject in ['chemistry', 'biology', 'elective_ict']:
            if data.get(f'{subject}_grade'):
                science_electives.append(subject)
                elective_checks[subject] = {
                    'actual': data[f'{subject}_grade'],
                    'passed': True,  # Just having it counts
                    'subject_name': subject.replace('_', ' ').title()
                }
        
        # Also check other electives as potential science subjects
        if data.get('other_elective_1_grade'):
            other_1 = data.get('other_elective_1', '').lower()
            if any(sci in other_1 for sci in ['chemistry', 'biology', 'ict', 'physics', 'science']):
                science_electives.append('other_elective_1')
                elective_checks['other_elective_1'] = {
                    'actual': data['other_elective_1_grade'],
                    'passed': True,
                    'subject_name': data.get('other_elective_1', 'Other Science Elective')
                }
        
        if data.get('other_elective_2_grade'):
            other_2 = data.get('other_elective_2', '').lower()
            if any(sci in other_2 for sci in ['chemistry', 'biology', 'ict', 'physics', 'science']):
                science_electives.append('other_elective_2')
                elective_checks['other_elective_2'] = {
                    'actual': data['other_elective_2_grade'],
                    'passed': True,
                    'subject_name': data.get('other_elective_2', 'Other Science Elective')
                }
        
        logger.info(f"Science electives found: {len(science_electives)} (need {criteria.science_electives_required})")
        
        if len(science_electives) < criteria.science_electives_required:
            recommendations.append(
                f"You need at least {criteria.science_electives_required} science electives. "
                f"You have {len(science_electives)}."
            )
        
        results['elective_subjects'] = elective_checks
        
        # Overall eligibility - REGULAR admission
        all_core_passed = all(check['passed'] for check in core_checks.values())
        all_required_electives_passed = all(
            check['passed'] for check in elective_checks.values()
            if check.get('is_required', False)
        )
        has_enough_science_electives = len(science_electives) >= criteria.science_electives_required
        
        meets_regular = (
            results['aggregate_check'] and
            all_core_passed and
            all_required_electives_passed and
            has_enough_science_electives
        )
        
        logger.info(f"Regular check: aggregate={results['aggregate_check']}, core={all_core_passed}, "
                   f"electives={all_required_electives_passed}, science={has_enough_science_electives}")
        
        # FEE-PAYING admission (relaxed requirements)
        # Fee-paying requires: aggregate within 24, C6 in core subjects, at least 1 science elective
        feepaying_aggregate_ok = aggregate_score <= 24
        feepaying_core_ok = all(
            self.grade_to_numerical(data[f'{subject}_grade']) <= 6  # C6 or better
            for subject in ['core_math', 'english', 'integrated_science', 'social_studies']
        )
        feepaying_has_science = len(science_electives) >= 1
        # At least one of elective math or physics (if not both, more lenient)
        has_one_key_elective = (
            (data.get('elective_math_grade') and self.grade_to_numerical(data['elective_math_grade']) <= 7) or
            (data.get('physics_grade') and self.grade_to_numerical(data['physics_grade']) <= 7)
        )
        
        meets_feepaying = (
            feepaying_aggregate_ok and
            feepaying_core_ok and
            feepaying_has_science and
            has_one_key_elective
        )
        
        logger.info(f"Fee-paying check: aggregate={feepaying_aggregate_ok}, core={feepaying_core_ok}, "
                   f"science={feepaying_has_science}, key_elective={has_one_key_elective}")
        
        results['overall_pass'] = meets_regular
        results['meets_regular'] = meets_regular
        results['meets_feepaying'] = meets_feepaying
        
        # Determine final eligibility based on admission type
        if admission_type == 'FEE_PAYING':
            final_eligible = meets_feepaying
        elif admission_type == 'MATURE':
            # Mature applicants: more lenient, mainly check core subjects
            final_eligible = all_core_passed and aggregate_score <= 30
        else:
            final_eligible = meets_regular
        
        # Generate recommendations
        if final_eligible:
            if admission_type == 'REGULAR' and meets_regular:
                final_rec = (
                    f"🎉 Congratulations! You meet the REGULAR admission requirements for {criteria.get_program_display()} at KNUST! "
                    f"Your aggregate score of {aggregate_score} is excellent. "
                    f"Next steps: 1) Purchase admission voucher, 2) Register on the portal, 3) Complete application form. "
                    f"Visit our guidelines section for detailed instructions."
                )
            elif admission_type == 'FEE_PAYING' and meets_feepaying:
                final_rec = (
                    f"✅ You qualify for FEE-PAYING admission to {criteria.get_program_display()} at KNUST! "
                    f"Your aggregate of {aggregate_score} meets the fee-paying criteria. "
                    f"Note: Fee-paying students pay higher tuition fees but follow the same curriculum. "
                    f"Next steps: Apply through the fee-paying stream on the KNUST portal."
                )
            elif admission_type == 'MATURE':
                final_rec = (
                    f"✅ You qualify as a MATURE APPLICANT for {criteria.get_program_display()} at KNUST! "
                    f"Ensure you meet age (25+) and experience (3 years) requirements. "
                    f"Contact admissions office for mature applicant application process."
                )
            else:
                final_rec = f"✅ You qualify for admission to {criteria.get_program_display()}!"
        else:
            # Not eligible for requested type, but check alternatives
            if not meets_regular and meets_feepaying and admission_type == 'REGULAR':
                final_rec = (
                    f"ℹ️ You do not meet REGULAR admission requirements for {criteria.get_program_display()}, "
                    f"BUT you qualify for FEE-PAYING admission! "
                    f"Fee-paying programs have slightly relaxed requirements and you meet those criteria. "
                    f"Consider applying through the fee-paying stream."
                )
                recommendations.append(
                    "💡 FEE-PAYING OPTION AVAILABLE: Your grades qualify you for fee-paying admission. "
                    "This pathway allows you to study the same program with slightly higher fees. "
                    "Many successful students have taken this route!"
                )
            else:
                final_rec = (
                    f"Unfortunately, you do not currently meet requirements for {criteria.get_program_display()} "
                    f"({admission_type.replace('_', ' ').title()} pathway). "
                    f"Please review the specific issues below and consider: "
                    f"1) Upgrading your grades if possible, 2) Applying as a fee-paying student (if regular fails), "
                    f"3) Considering alternative programs, 4) Contacting KNUST admissions for guidance."
                )
        
        recommendations.insert(0, final_rec)
        
        return {
            'is_eligible': final_eligible,
            'meets_regular': meets_regular,
            'meets_feepaying': meets_feepaying,
            'admission_type': admission_type,
            'details': results,
            'recommendations': '\n\n'.join(recommendations)
        }
    
    def create(self, request, *args, **kwargs):
        """Create eligibility check and return results"""
        input_serializer = EligibilityCheckInputSerializer(data=request.data)
        
        if not input_serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid input data',
                'errors': input_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Recalculate aggregate using WASSCE formula: Best 3 core + Best 3 electives
        validated_data = input_serializer.validated_data.copy()
        
        # Best 3 core: English, Math, and best of (Science or Social Studies)
        core_grades = [
            self.grade_to_numerical(validated_data['core_math_grade']),
            self.grade_to_numerical(validated_data['english_grade']),
            min(
                self.grade_to_numerical(validated_data['integrated_science_grade']),
                self.grade_to_numerical(validated_data['social_studies_grade'])
            )
        ]
        
        # Best 3 electives
        elective_grades = []
        for field in ['elective_math_grade', 'physics_grade', 'chemistry_grade', 
                     'biology_grade', 'elective_ict_grade', 'other_elective_1_grade', 
                     'other_elective_2_grade']:
            if validated_data.get(field):
                elective_grades.append(self.grade_to_numerical(validated_data[field]))
        
        elective_grades.sort()  # Sort ascending (best first)
        best_3_electives = elective_grades[:3] if len(elective_grades) >= 3 else elective_grades
        
        # Recalculate aggregate
        validated_data['aggregate_score'] = sum(core_grades) + sum(best_3_electives)
        
        # Perform eligibility check
        check_result = self.perform_eligibility_check(validated_data, request)
        
        # Create eligibility check record
        eligibility_data = {
            **validated_data,
            'is_eligible': check_result['is_eligible'],
            'meets_regular_requirements': check_result.get('meets_regular', False),
            'meets_feepaying_requirements': check_result.get('meets_feepaying', False),
            'eligibility_details': check_result['details'],
            'recommendations': check_result['recommendations'],
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
        
        serializer = self.get_serializer(data=eligibility_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'status': 'success',
            'message': 'Eligibility check completed',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def my_checks(self, request):
        """Get previous eligibility checks by email"""
        email = request.query_params.get('email')
        if not email:
            return Response({
                'status': 'error',
                'message': 'Email parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        checks = self.queryset.filter(email=email).order_by('-checked_at')[:10]
        
        serializer = self.get_serializer(checks, many=True)
        return Response({
            'status': 'success',
            'message': 'Previous checks retrieved',
            'data': serializer.data,
            'meta': {
                'total': checks.count()
            }
        })


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for FAQs
    """
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        category = request.query_params.get('category', None)
        queryset = self.get_queryset()
        
        if category:
            queryset = queryset.filter(category=category.upper())
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Group by category
        grouped_faqs = {}
        for faq in serializer.data:
            cat = faq['category']
            if cat not in grouped_faqs:
                grouped_faqs[cat] = []
            grouped_faqs[cat].append(faq)
        
        return Response({
            'status': 'success',
            'message': 'FAQs retrieved successfully',
            'data': serializer.data,
            'meta': {
                'grouped': grouped_faqs,
                'total': queryset.count()
            }
        })


class ImportantDateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for important dates
    """
    queryset = ImportantDate.objects.filter(is_active=True)
    serializer_class = ImportantDateSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        academic_year = request.query_params.get('academic_year', None)
        queryset = self.get_queryset()
        
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        # Separate upcoming and past dates
        today = timezone.now().date()
        upcoming = queryset.filter(event_date__gte=today)
        past = queryset.filter(event_date__lt=today).order_by('-event_date')[:5]
        
        serializer = self.get_serializer(queryset, many=True)
        upcoming_serializer = self.get_serializer(upcoming, many=True)
        past_serializer = self.get_serializer(past, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Important dates retrieved successfully',
            'data': {
                'all': serializer.data,
                'upcoming': upcoming_serializer.data,
                'past': past_serializer.data
            },
            'meta': {
                'total': queryset.count(),
                'upcoming_count': upcoming.count(),
                'next_event': upcoming_serializer.data[0] if upcoming_serializer.data else None
            }
        })


class WhatsAppHelpdeskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WhatsApp helpdesk access
    Students verify admission with Application ID, then get WhatsApp group link
    """
    queryset = WhatsAppHelpdesk.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    serializer_class = WhatsAppHelpdeskSerializer
    
    @action(detail=False, methods=['post'])
    def get_link(self, request):
        """
        Verify student admission and provide WhatsApp group link
        
        Process:
        1. Student provides Application ID
        2. System checks if ID exists in KNUST Admissions (scraped data)
        3. If admitted, provide appropriate WhatsApp group link based on program
        4. Log access for tracking
        """
        input_serializer = WhatsAppHelpdeskInputSerializer(data=request.data)
        
        if not input_serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid application ID',
                'errors': input_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        application_id = input_serializer.validated_data['application_id']
        
        # Step 1: Check if application ID exists in KNUST Admissions database (scraped data)
        try:
            knust_admission = KNUSTAdmission.objects.get(applicant_id=application_id)
        except KNUSTAdmission.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Application ID not found in admission records',
                'data': {
                    'application_id': application_id,
                    'help_text': 'This application ID was not found in our admission records. Please verify your application ID or check back later if results are still being processed.'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Step 2: Determine program from admission record
        # Extract program from programme field (e.g., "Computer Science" -> CS)
        programme_lower = knust_admission.programme.lower()
        if 'computer science' in programme_lower:
            program_code = 'CS'
        elif 'information technology' in programme_lower or 'it' in programme_lower:
            program_code = 'IT'
        else:
            return Response({
                'status': 'error',
                'message': 'Program not eligible for WhatsApp helpdesk',
                'data': {
                    'application_id': application_id,
                    'applicant_name': knust_admission.name,
                    'programme': knust_admission.programme,
                    'help_text': 'The WhatsApp helpdesk is only available for Computer Science and Information Technology programs.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Step 3: Get WhatsApp group for this program
        try:
            helpdesk = WhatsAppHelpdesk.objects.get(
                program=program_code,
                group_type='ADMISSION',
                is_active=True
            )
        except WhatsAppHelpdesk.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'WhatsApp group not yet configured',
                'data': {
                    'application_id': application_id,
                    'applicant_name': knust_admission.name,
                    'programme': knust_admission.programme,
                    'help_text': 'The WhatsApp helpdesk group for your program is not yet available. Please check back later or contact the admissions office.'
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Step 4: Log access and update counter
        WhatsAppAccessLog.objects.create(
            helpdesk=helpdesk,
            application_id=application_id,
            student_name=knust_admission.name,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        helpdesk.access_count += 1
        helpdesk.save(update_fields=['access_count'])
        
        # Step 5: Return success with WhatsApp link
        return Response({
            'status': 'success',
            'message': 'Your admission has been verified! Join the WhatsApp group below.',
            'data': {
                'application_id': application_id,
                'student_name': knust_admission.name,
                'programme': knust_admission.programme,
                'program_code': program_code,
                'program_display': helpdesk.get_program_display(),
                'whatsapp_group_link': helpdesk.whatsapp_group_link,
                'group_description': helpdesk.group_description,
                'academic_year': helpdesk.academic_year,
                'welcome_message': f'🎉 Congratulations {knust_admission.name}! You have been admitted to {knust_admission.programme}. Click the link below to join your program\'s WhatsApp group for updates, support, and to connect with fellow students.'
            }
        })


class AccommodationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for student accommodation management.
    Allows admitted students to update their accommodation details.
    
    Flow:
    1. verify_identity: Student enters applicant_id + phone_number
    2. verify_name: Student enters their name to match against admission record
    3. update_accommodation: Student enters accommodation details
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='verify-identity')
    def verify_identity(self, request):
        """
        Step 1: Verify student identity using applicant_id and phone_number.
        Checks if the applicant_id exists in KNUSTAdmission and if the phone
        number matches one registered in accounts (optional check).
        Also checks if accommodation has already been submitted (one-time only).
        """
        serializer = AccommodationVerifySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid input provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        applicant_id = serializer.validated_data['applicant_id']
        phone_number = serializer.validated_data['phone_number']
        
        # Check if applicant_id exists in admission records
        try:
            admission = KNUSTAdmission.objects.get(applicant_id=applicant_id)
        except KNUSTAdmission.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Application ID not found',
                'data': {
                    'applicant_id': applicant_id,
                    'help_text': 'This application ID was not found in our admission records. Please verify your application ID and try again.'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if accommodation has already been verified (one-time update only)
        if admission.accommodation_verified:
            # Determine program for WhatsApp group
            programme_lower = admission.programme.lower()
            if 'computer science' in programme_lower:
                program_code = 'CS'
            elif 'information technology' in programme_lower or 'it' in programme_lower:
                program_code = 'IT'
            else:
                program_code = None
            
            # Check for Academic WhatsApp group
            whatsapp_info = None
            if program_code:
                try:
                    academic_group = WhatsAppHelpdesk.objects.get(
                        program=program_code,
                        group_type='ACADEMIC',
                        is_active=True
                    )
                    # Generate access token for this user
                    token = self._generate_group_token(applicant_id, program_code)
                    whatsapp_info = {
                        'available': True,
                        'group_name': f'{academic_group.get_program_display()} Official Group',
                        'description': academic_group.group_description,
                        'token': token,
                        'program_code': program_code,
                    }
                except WhatsAppHelpdesk.DoesNotExist:
                    whatsapp_info = {
                        'available': False,
                        'message': 'Official group not yet available. Please check back later.'
                    }
            
            return Response({
                'status': 'already_submitted',
                'message': 'Accommodation details have already been submitted',
                'data': {
                    'applicant_id': applicant_id,
                    'student_name': admission.name,
                    'programme': admission.programme,
                    'programme_code': program_code,
                    'accommodation': {
                        'type': admission.get_accommodation_type_display() if admission.accommodation_type else None,
                        'hall': admission.get_hall_name_display() if admission.hall_name else None,
                        'hostel': admission.hostel_name,
                        'room': admission.room_number,
                    },
                    'phone_number': admission.phone_number,
                    'updated_at': admission.accommodation_updated_at.isoformat() if admission.accommodation_updated_at else None,
                    'whatsapp_group': whatsapp_info,
                    'help_text': "You have already submitted your accommodation details. Each student can only submit once. If you need to make changes, please contact the CSS President."
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store the phone number for verification in next step
        # We'll verify the name in the next step
        return Response({
            'status': 'success',
            'message': 'Application ID verified successfully',
            'data': {
                'applicant_id': applicant_id,
                'phone_number': phone_number,
                'programme': admission.programme,
                'has_accommodation_data': bool(admission.accommodation_type),
                'current_accommodation': {
                    'type': admission.get_accommodation_type_display() if admission.accommodation_type else None,
                    'hall': admission.get_hall_name_display() if admission.hall_name else None,
                    'hostel': admission.hostel_name,
                    'room': admission.room_number,
                } if admission.accommodation_type else None,
                'next_step': 'verify_name',
                'help_text': 'Please enter your name as it appears on your admission letter for verification.'
            }
        })
    
    @action(detail=False, methods=['post'], url_path='verify-name')
    def verify_name(self, request):
        """
        Step 2: Verify student name matches the admission record.
        Uses fuzzy matching to compare names.
        """
        serializer = AccommodationNameVerifySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid input provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        applicant_id = serializer.validated_data['applicant_id']
        first_name = serializer.validated_data['first_name']
        last_name = serializer.validated_data['last_name']
        other_names = serializer.validated_data.get('other_names', '')
        
        # Get the admission record
        try:
            admission = KNUSTAdmission.objects.get(applicant_id=applicant_id)
        except KNUSTAdmission.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Application ID not found',
                'data': {'applicant_id': applicant_id}
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get stored name and clean it
        stored_name = admission.name.upper().strip()
        # Clean stored name: remove punctuation and normalize spaces
        import re
        stored_name_clean = re.sub(r'[,.-]', ' ', stored_name)  # Replace punctuation with spaces
        stored_name_clean = re.sub(r'\s+', ' ', stored_name_clean).strip()  # Normalize spaces
        stored_name_parts = set(stored_name_clean.split())
        
        # Build input name parts and clean them
        first_name_clean = first_name.upper().strip()
        last_name_clean = last_name.upper().strip()
        other_names_clean = other_names.upper().strip() if other_names else ""
        
        input_name_parts = set()
        
        # Split compound names (e.g., "DAN- MORTON" -> ["DAN", "MORTON"])
        for name_part in [first_name_clean, last_name_clean]:
            clean_part = re.sub(r'[,.-]', ' ', name_part)  # Replace punctuation with spaces
            clean_part = re.sub(r'\s+', ' ', clean_part).strip()  # Normalize spaces
            for sub_part in clean_part.split():
                if sub_part:  # Only add non-empty parts
                    input_name_parts.add(sub_part)
        
        # Add other names if provided
        if other_names_clean:
            clean_other = re.sub(r'[,.-]', ' ', other_names_clean)
            clean_other = re.sub(r'\s+', ' ', clean_other).strip()
            for sub_part in clean_other.split():
                if sub_part:
                    input_name_parts.add(sub_part)
        
        # Check if first and last name components are in stored name
        first_in_stored = first_name_clean in stored_name or any(part in stored_name_clean for part in re.sub(r'[,.-]', ' ', first_name_clean).split())
        last_in_stored = last_name_clean in stored_name or any(part in stored_name_clean for part in re.sub(r'[,.-]', ' ', last_name_clean).split())
        
        # Alternative: check intersection of name parts
        matching_parts = stored_name_parts.intersection(input_name_parts)
        match_percentage = len(matching_parts) / max(len(stored_name_parts), len(input_name_parts)) * 100 if max(len(stored_name_parts), len(input_name_parts)) > 0 else 0
        
        # Require at least both first and last name to match, or 60% of name parts (lowered threshold)
        is_match = (first_in_stored and last_in_stored) or match_percentage >= 60
        
        if not is_match:
            return Response({
                'status': 'error',
                'message': 'Name does not match our records',
                'data': {
                    'applicant_id': applicant_id,
                    'entered_name': f'{first_name} {other_names} {last_name}'.strip(),
                    'help_text': 'The name you entered does not match the name on your admission record. Please enter your full name exactly as it appears on your admission letter.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Name verified successfully
        return Response({
            'status': 'success',
            'message': 'Name verified successfully',
            'data': {
                'applicant_id': applicant_id,
                'verified_name': admission.name,
                'programme': admission.programme,
                'next_step': 'update_accommodation',
                'help_text': 'Your identity has been verified. Please enter your accommodation details.',
                'accommodation_options': {
                    'types': [
                        {'value': 'TRADITIONAL_HALL', 'label': 'Traditional Hall'},
                        {'value': 'HOSTEL', 'label': 'Hostel'},
                        {'value': 'OFF_CAMPUS', 'label': 'Off Campus'},
                    ],
                    'halls': [
                        {'value': 'UNITY_HALL', 'label': 'Unity Hall (Conti)'},
                        {'value': 'QUEENS_HALL', 'label': "Queen's Hall"},
                        {'value': 'INDEPENDENCE_HALL', 'label': 'Independence Hall (Indece)'},
                        {'value': 'AFRICA_HALL', 'label': 'Africa Hall (Katanga)'},
                        {'value': 'REPUBLIC_HALL', 'label': 'Republic Hall (Rep)'},
                        {'value': 'UNIVERSITY_HALL', 'label': 'University Hall (Brunei)'},
                        {'value': 'OTHER', 'label': 'Other'},
                    ],
                    'campus_status': [
                        {'value': 'ON_CAMPUS', 'label': 'On Campus'},
                        {'value': 'OFF_CAMPUS', 'label': 'Off Campus'},
                    ]
                }
            }
        })
    
    @action(detail=False, methods=['post'], url_path='update')
    def update_accommodation(self, request):
        """
        Step 3: Update student accommodation details.
        Requires prior verification through verify_identity and verify_name.
        After successful update, returns the Academic WhatsApp group link.
        """
        serializer = AccommodationUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid accommodation details provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        applicant_id = serializer.validated_data['applicant_id']
        
        # Get the admission record
        try:
            admission = KNUSTAdmission.objects.get(applicant_id=applicant_id)
        except KNUSTAdmission.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Application ID not found',
                'data': {'applicant_id': applicant_id}
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already submitted (one-time only)
        if admission.accommodation_verified:
            return Response({
                'status': 'error',
                'message': 'Accommodation details have already been submitted. You cannot update again.',
                'data': {'applicant_id': applicant_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update accommodation fields
        admission.accommodation_type = serializer.validated_data['accommodation_type']
        admission.campus_status = serializer.validated_data['campus_status']
        admission.phone_number = serializer.validated_data['phone_number']
        
        # Set hall/hostel based on accommodation type
        accommodation_type = serializer.validated_data['accommodation_type']
        if accommodation_type == 'TRADITIONAL_HALL':
            admission.hall_name = serializer.validated_data.get('hall_name')
            admission.hostel_name = None
            admission.room_number = serializer.validated_data.get('room_number', '')
        elif accommodation_type == 'HOSTEL':
            admission.hall_name = None
            admission.hostel_name = serializer.validated_data.get('hostel_name', '')
            admission.room_number = serializer.validated_data.get('room_number', '')
        else:  # OFF_CAMPUS
            admission.hall_name = None
            admission.hostel_name = None
            admission.room_number = None
        
        # Mark as verified and set update timestamp
        admission.accommodation_verified = True
        admission.accommodation_updated_at = timezone.now()
        
        # Save the changes
        admission.save(update_fields=[
            'accommodation_type', 'campus_status', 'hall_name', 'hostel_name',
            'room_number', 'phone_number', 'accommodation_verified', 'accommodation_updated_at'
        ])
        
        # Build response with updated data
        accommodation_display = {
            'TRADITIONAL_HALL': f'{admission.get_hall_name_display()} - Room {admission.room_number}' if admission.room_number else admission.get_hall_name_display(),
            'HOSTEL': f'{admission.hostel_name} - Room {admission.room_number}' if admission.room_number else admission.hostel_name,
            'OFF_CAMPUS': 'Off Campus'
        }.get(admission.accommodation_type, 'Unknown')
        
        # Determine program code from programme field
        programme_lower = admission.programme.lower()
        if 'computer science' in programme_lower:
            program_code = 'CS'
        elif 'information technology' in programme_lower or 'it' in programme_lower:
            program_code = 'IT'
        else:
            program_code = None
        
        # Get Academic WhatsApp group for this program
        whatsapp_group = None
        if program_code:
            try:
                academic_group = WhatsAppHelpdesk.objects.get(
                    program=program_code,
                    group_type='ACADEMIC',
                    is_active=True
                )
                whatsapp_group = {
                    'name': f'{academic_group.get_program_display()} Official Group',
                    'link': academic_group.whatsapp_group_link,
                    'description': academic_group.group_description,
                    'academic_year': academic_group.academic_year,
                }
                
                # Log access
                WhatsAppAccessLog.objects.create(
                    helpdesk=academic_group,
                    application_id=applicant_id,
                    student_name=admission.name,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                academic_group.access_count += 1
                academic_group.save(update_fields=['access_count'])
                
            except WhatsAppHelpdesk.DoesNotExist:
                pass  # No academic group configured yet
        
        return Response({
            'status': 'success',
            'message': 'Accommodation details updated successfully!',
            'data': {
                'applicant_id': applicant_id,
                'student_name': admission.name,
                'programme': admission.programme,
                'programme_code': program_code,
                'accommodation': {
                    'type': admission.get_accommodation_type_display(),
                    'campus_status': admission.get_campus_status_display(),
                    'hall_name': admission.get_hall_name_display() if admission.hall_name else None,
                    'hostel_name': admission.hostel_name,
                    'room_number': admission.room_number,
                    'display': accommodation_display,
                },
                'phone_number': admission.phone_number,
                'updated_at': admission.accommodation_updated_at.isoformat() if admission.accommodation_updated_at else None,
                'verified': admission.accommodation_verified,
                'success_message': f'🏠 Your accommodation has been recorded as: {accommodation_display}',
                'whatsapp_group': whatsapp_group,
            }
        })
    
    @action(detail=False, methods=['get'], url_path='check/(?P<applicant_id>[^/.]+)')
    def check_accommodation(self, request, applicant_id=None):
        """
        Check current accommodation status for an applicant.
        Useful for checking if accommodation has been updated.
        """
        if not applicant_id:
            return Response({
                'status': 'error',
                'message': 'Application ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            admission = KNUSTAdmission.objects.get(applicant_id=applicant_id)
        except KNUSTAdmission.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Application ID not found',
                'data': {'applicant_id': applicant_id}
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not admission.accommodation_type:
            return Response({
                'status': 'success',
                'message': 'No accommodation details found',
                'data': {
                    'applicant_id': applicant_id,
                    'has_accommodation': False,
                    'help_text': 'You have not yet submitted your accommodation details.'
                }
            })
        
        return Response({
            'status': 'success',
            'message': 'Accommodation details found',
            'data': {
                'applicant_id': applicant_id,
                'student_name': admission.name,
                'has_accommodation': True,
                'accommodation': {
                    'type': admission.get_accommodation_type_display(),
                    'campus_status': admission.get_campus_status_display(),
                    'hall_name': admission.get_hall_name_display() if admission.hall_name else None,
                    'hostel_name': admission.hostel_name,
                    'room_number': admission.room_number,
                },
                'phone_number': admission.phone_number,
                'updated_at': admission.accommodation_updated_at.isoformat() if admission.accommodation_updated_at else None,
                'verified': admission.accommodation_verified
            }
        })
    
    def _generate_group_token(self, applicant_id, program_code):
        """Generate a time-limited token for WhatsApp group access"""
        # Token valid for 5 minutes
        timestamp = int(time.time())
        expiry = timestamp + 300  # 5 minutes
        secret = "css_whatsapp_secret_2025"  # In production, use Django settings
        data = f"{applicant_id}:{program_code}:{expiry}:{secret}"
        token = hashlib.sha256(data.encode()).hexdigest()[:32]
        return f"{token}:{expiry}"
    
    def _verify_group_token(self, applicant_id, program_code, token_string):
        """Verify a group access token"""
        try:
            token, expiry_str = token_string.split(':')
            expiry = int(expiry_str)
            
            # Check if expired
            if int(time.time()) > expiry:
                return False
            
            # Regenerate and compare
            secret = "css_whatsapp_secret_2025"
            data = f"{applicant_id}:{program_code}:{expiry}:{secret}"
            expected_token = hashlib.sha256(data.encode()).hexdigest()[:32]
            return token == expected_token
        except Exception:
            return False
    
    @action(detail=False, methods=['post'], url_path='get-group-access')
    def get_group_access(self, request):
        """
        Generate a secure, time-limited token for WhatsApp group access.
        Only for verified/submitted students.
        """
        applicant_id = request.data.get('applicant_id')
        
        if not applicant_id:
            return Response({
                'status': 'error',
                'message': 'Application ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            admission = KNUSTAdmission.objects.get(applicant_id=applicant_id)
        except KNUSTAdmission.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Application ID not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Must have submitted accommodation
        if not admission.accommodation_verified:
            return Response({
                'status': 'error',
                'message': 'Please complete your accommodation registration first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine program
        programme_lower = admission.programme.lower()
        if 'computer science' in programme_lower:
            program_code = 'CS'
        elif 'information technology' in programme_lower or 'it' in programme_lower:
            program_code = 'IT'
        else:
            return Response({
                'status': 'error',
                'message': 'Program not eligible for WhatsApp group'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if academic group exists
        try:
            academic_group = WhatsAppHelpdesk.objects.get(
                program=program_code,
                group_type='ACADEMIC',
                is_active=True
            )
        except WhatsAppHelpdesk.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Official group not yet available. Please check back later.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate token
        token = self._generate_group_token(applicant_id, program_code)
        
        return Response({
            'status': 'success',
            'message': 'Group access token generated',
            'data': {
                'applicant_id': applicant_id,
                'program_code': program_code,
                'group_name': f'{academic_group.get_program_display()} Official Group',
                'token': token,
                'expires_in': 300,  # 5 minutes
            }
        })
    
    @action(detail=False, methods=['get'], url_path='join-group/(?P<applicant_id>[^/.]+)/(?P<token>[^/.]+)')
    def join_group_redirect(self, request, applicant_id=None, token=None):
        """
        Secure redirect to WhatsApp group.
        Validates token and redirects to actual WhatsApp link.
        """
        if not applicant_id or not token:
            return HttpResponseForbidden("Invalid request")
        
        try:
            admission = KNUSTAdmission.objects.get(applicant_id=applicant_id)
        except KNUSTAdmission.DoesNotExist:
            return HttpResponseForbidden("Invalid application ID")
        
        # Determine program
        programme_lower = admission.programme.lower()
        if 'computer science' in programme_lower:
            program_code = 'CS'
        elif 'information technology' in programme_lower or 'it' in programme_lower:
            program_code = 'IT'
        else:
            return HttpResponseForbidden("Program not eligible")
        
        # Verify token
        if not self._verify_group_token(applicant_id, program_code, token):
            return HttpResponseForbidden("Link expired or invalid. Please generate a new link.")
        
        # Get the actual WhatsApp link
        try:
            academic_group = WhatsAppHelpdesk.objects.get(
                program=program_code,
                group_type='ACADEMIC',
                is_active=True
            )
        except WhatsAppHelpdesk.DoesNotExist:
            return HttpResponseForbidden("Group not available")
        
        # Log access
        WhatsAppAccessLog.objects.create(
            helpdesk=academic_group,
            application_id=applicant_id,
            student_name=admission.name,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        academic_group.access_count += 1
        academic_group.save(update_fields=['access_count'])
        
        # Redirect to WhatsApp
        return redirect(academic_group.whatsapp_group_link)


