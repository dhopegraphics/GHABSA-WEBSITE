"""
Admin views for KNUST Admissions Scraper
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .scraper import KNUSTAdmissionsScraper
from .models import KNUSTAdmission, get_current_academic_year
import os
import tempfile


@staff_member_required
def scraper_dashboard(request):
    """Display the scraper dashboard with Excel data and database stats."""
    scraper = KNUSTAdmissionsScraper()
    
    # Get file info
    file_info = scraper.get_file_info()
    
    # Get Excel data for display
    headers, rows = scraper.get_excel_data(limit=50)
    
    # Get database stats
    db_total = KNUSTAdmission.objects.count()
    
    # Get stats by academic year
    year_stats = scraper.get_stats_by_academic_year()
    
    # Check for mismatch between Excel and DB (any difference)
    has_mismatch = False
    if file_info:
        has_mismatch = file_info['total_records'] != db_total
    
    # Get unique academic years for dropdown
    academic_years = KNUSTAdmission.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    context = {
        'file_info': file_info,
        'headers': headers,
        'rows': rows,
        'has_data': len(rows) > 0,
        'db_total': db_total,
        'has_mismatch': has_mismatch,
        'year_stats': year_stats,
        'academic_years': list(academic_years),
        'current_academic_year': get_current_academic_year(),
        'title': 'KNUST CS/IT Admissions Scraper',
    }
    
    return render(request, 'admin/admissions/scraper_dashboard.html', context)


@staff_member_required
@require_http_methods(["POST"])
def run_scraper(request):
    """Run the scraper and return JSON response."""
    scraper = KNUSTAdmissionsScraper()
    
    success, message, stats = scraper.scrape_and_update()
    
    return JsonResponse({
        'success': success,
        'message': message,
        'stats': stats
    })


@staff_member_required
@require_http_methods(["POST"])
def clean_excel_duplicates(request):
    """Clean duplicate entries from the Excel file."""
    scraper = KNUSTAdmissionsScraper()
    
    removed, total_after = scraper.clean_excel_duplicates()
    db_total = KNUSTAdmission.objects.count()
    
    return JsonResponse({
        'success': True,
        'message': f'✅ Removed {removed} duplicate entries. Excel now has {total_after} records (DB: {db_total}).',
        'removed': removed,
        'excel_total': total_after,
        'db_total': db_total
    })


@staff_member_required
@require_http_methods(["POST"])
def sync_excel_with_db(request):
    """Rebuild Excel file from database to ensure sync."""
    scraper = KNUSTAdmissionsScraper()
    
    success, message, total = scraper.sync_excel_with_database()
    db_total = KNUSTAdmission.objects.count()
    
    return JsonResponse({
        'success': success,
        'message': message,
        'excel_total': total,
        'db_total': db_total
    })


@staff_member_required
def download_excel(request):
    """Download the Excel file."""
    from django.http import FileResponse, Http404
    
    scraper = KNUSTAdmissionsScraper()
    
    if not os.path.exists(scraper.excel_file):
        raise Http404("Excel file not found. Please run the scraper first.")
    
    response = FileResponse(
        open(scraper.excel_file, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="knust_admissions.xlsx"'
    
    return response


@staff_member_required
@require_http_methods(["POST"])
def upload_excel(request):
    """Upload and import Excel file with admission data."""
    if 'file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'message': 'No file uploaded'
        })
    
    uploaded_file = request.FILES['file']
    academic_year = request.POST.get('academic_year', get_current_academic_year())
    
    # Validate file type
    if not uploaded_file.name.endswith(('.xlsx', '.xls')):
        return JsonResponse({
            'success': False,
            'message': 'Please upload an Excel file (.xlsx or .xls)'
        })
    
    # Save to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        # Import data
        scraper = KNUSTAdmissionsScraper()
        success, message, stats = scraper.import_from_excel(tmp_path, academic_year)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return JsonResponse({
            'success': success,
            'message': message,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing file: {str(e)}'
        })


@staff_member_required
def get_year_stats(request):
    """Get admission statistics by academic year."""
    scraper = KNUSTAdmissionsScraper()
    stats = scraper.get_stats_by_academic_year()
    
    return JsonResponse({
        'success': True,
        'stats': stats
    })
