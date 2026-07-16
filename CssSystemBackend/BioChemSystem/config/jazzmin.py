from .brand import BRAND_NAME, FRONTEND_URL

# DOMAIN ON WHICH THE FRONTEND IS HOSTED
FRONTEND_HOSTURL = FRONTEND_URL


JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": f"{BRAND_NAME} Department Administration",
    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": f"{BRAND_NAME} Department Executives",
    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": f"{BRAND_NAME} Department",
    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": "logos/logo.png",
    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    # dont provide a correct logo path to prevent the login form shift down
    # and dont comment it otherwise it will default to the site icon which will cause the same problem
    "login_logo": "logos/logo.png",
    # Logo to use for login form in dark themes (defaults to login_logo)
    "login_logo_dark": None,
    # CSS classes that are applied to the logo above
    # "site_logo_classes": "img-circle",
    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,
    # Welcome text on the login screen
    "welcome_sign": "Welcome, Please login with your Executives Credentials",
    # Copyright on the footer
    "copyright": f"{BRAND_NAME} Department Execs",
    # List of model admins to search from the search bar, search bar omitted if excluded
    # If you want to use a single search field you dont need to use a list, you can use a simple string
    "search_model": ["accounts.CustomUser", "events.Event", "timeline.Timeline", "helpdesk.HelpDeskRequest"],
    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,
    ############
    # Top Menu #
    ############
    # Links to put along the top menu
    "topmenu_links": [
        # Url that gets reversed (Permissions can be added)
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        # external url that opens in a new window (Permissions can be added)
        {
            "name": "Main Site",
            "url": FRONTEND_HOSTURL,
            "new_window": True,
        },
        {
            "name": "Knust",
            "url": "https://www.knust.edu.gh",
            "new_window": True,
        },
        # model admin to link to (Permissions checked against model)
        # {"model": "auth.User"},
        # App with dropdown menu to all its models pages (Permissions checked against models)
        # {"app": "books"},  # Commented out - no books app installed
    ],
    #############
    # User Menu #
    #############
    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        # {
        #     "name": "Support",
        #     "url": "https://github.com/Bookmie-Devs/BIO-CHEM-KNUST-Frontend",
        #     "new_window": True,
        # },
        {"model": "auth.user"},
    ],
    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": True,
    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],
    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],
    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": [
        "auth",
        "accounts",
        "core",
        "helpdesk",
        "timetable_system",
        "academics.course",
        "academics.lecturer",
        "academics.acadamicslides",
        "academics.pastquestions",
        "news",
        "executives.executiveposition",
        "executives.executive",
        "executives.executiveprofile",
        "events",
        "timeline",
    ],
    # Custom links to append to app groups, keyed on app name
    "custom_links": {
        "news": [
            {
                "name": "See News Feed",
                "url": f"{FRONTEND_HOSTURL}/blogs?page=1",
                "icon": "fas fa-comments",
                "new_window": True,
                # "permissions": ["news.view_news"],
            }
        ],
        "helpdesk": [
            {
                "name": "View HelpDesk Frontend",
                "url": f"{FRONTEND_HOSTURL}/helpdesk",
                "icon": "fas fa-external-link-alt",
                "new_window": True,
            },
            {
                "name": "📊 Executive Dashboard",
                "url": "admin:helpdesk_contentreport_changelist",
                "icon": "fas fa-chart-line",
            }
        ]
    },
    # Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts.customuser": "fas fa-user",
        "news.news": "fa-solid fa-newspaper",
        "events.event": "fa-solid fa-calendar-days",
        "events.eventrsvp": "fa-solid fa-calendar-check",
        "events.eventregistration": "fa-solid fa-clipboard-list",
        "events.teammember": "fa-solid fa-users",
        "events.syncmemoalbum": "fa-solid fa-images",
        "events.syncmemophoto": "fa-solid fa-image",
        "events.syncmemolike": "fa-solid fa-heart",
        "events.syncmemocomment": "fa-solid fa-comment",
        "events.syncmemocommentlike": "fa-solid fa-thumbs-up",
        "timeline.timeline": "fa-solid fa-timeline",
        "academics.course": "fa-solid fa-person-chalkboard",
        "academics.lecturer": "fa-solid fa-chalkboard-user",
        "academics.pastquestions": "fa-solid fa-file-pdf",
        "academics.academicslides": "fa-regular fa-file-pdf",
        "academics.onlinetutorialtips": "fa-solid fa-link",
        "timetable_system.examinationschedule": "fa-solid fa-clock",
        "executives.executive": "fa-solid fa-user-tie",
        "executives.executivesociallinks": "fa-brands fa-github",
        "executives.executiveposition": "fa-solid fa-suitcase",
        "executives.committee": "fa-solid fa-users",
        "executives.appointee": "fa-solid fa-user-tag",
        "executives.appointeesociallinks": "fa-solid fa-link",
        "executives.appointeecontactdetails": "fa-solid fa-address-card",
        "executives.appointeepermission": "fa-solid fa-user-shield",
        "executives.permissionauditlog": "fa-solid fa-clipboard-list",
        "core.notifyuser": "fa-solid fa-message",
        "core.contactus": "fa-solid fa-phone",
        "advertisements.advertisement": "fa-solid fa-rectangle-ad",
        "products.productpayment": "fa-solid fa-money-bill",
        "products.product": "fa-solid fa-cart-shopping",
        "academics.internshipopportunities": "fa-solid fa-handshake-angle",
        "helpdesk": "fas fa-life-ring",
        "helpdesk.helpdeskcategory": "fas fa-tags",
        "helpdesk.helpdeskrequest": "fas fa-question-circle",
        "helpdesk.helpdeskresponse": "fas fa-comment-dots",
        "helpdesk.contentreport": "fas fa-flag",
        "helpdesk.userreputation": "fas fa-trophy",
        "helpdesk.helpdesknotification": "fas fa-bell",
        "helpdesk.requestbookmark": "fas fa-bookmark",
        "helpdesk.responsevote": "fas fa-thumbs-up",
        "helpdesk.codesnippet": "fa-solid fa-code",
        "helpdesk.requestimage": "fa-solid fa-image",
        "helpdesk.responsecodesnippet": "fa-solid fa-file-code",
        "helpdesk.responselink": "fa-solid fa-link",
        "helpdesk.responsereply": "fa-solid fa-reply",
        "helpdesk.requestview": "fa-solid fa-eye",
        "helpdesk.contentreport": "fa-solid fa-exclamation-triangle",
        "helpdesk.requestbookmark": "fa-solid fa-bookmark",
        "helpdesk.responsevote": "fa-solid fa-thumbs-up",
        "helpdesk.helpdesknotification": "fa-solid fa-bell",
        "helpdesk.requestimage": "fa-solid fa-image",
        "helpdesk.responsecodesnippet": "fa-solid fa-file-code",
        "helpdesk.responsevote": "fa-solid fa-hand-point-up",
        "helpdesk.requestview": "fa-solid fa-binoculars",
        "helpdesk.requestbookmark": "fa-solid fa-bookmark",
        # CodeQuest app icons
        "codequest": "fa-solid fa-brain",
        "codequest.codequestevent": "fa-solid fa-calendar-days",
        "codequest.codequestparticipant": "fa-solid fa-user-graduate",
        "codequest.codequestgroup": "fa-solid fa-users",
        "codequest.codequestproject": "fa-solid fa-lightbulb",
        "codequest.codequestconsultant": "fa-solid fa-chalkboard-user",
        "codequest.projecttask": "fa-solid fa-tasks",
        "codequest.projectmanagercandidate": "fa-solid fa-user",
        "codequest.projectmanagervote": "fa-solid fa-check",
        "codequest.groupmemberrole": "fa-solid fa-user-tag",
        "codequest.projectscore": "fa-solid fa-square-poll-vertical",
        "codequest.finalprojectscore": "fa-solid fa-award",
        "codequest.scoringcriteria": "fa-solid fa-list-check",
        "codequest.codequestfacilitator": "fa-solid fa-chalkboard-user",
        "codequest.consultantgroupassignment": "fa-solid fa-handshake",
        # Additional app icons
        "payments": "fa-solid fa-credit-card",
        "payments.payment": "fa-solid fa-receipt",
        "payments.paymentgateway": "fa-solid fa-plug",
        "payments.currency": "fa-solid fa-money-bill-wave",
        "payments.transaction": "fa-solid fa-file-invoice-dollar",
        "payments.paymentsession": "fa-solid fa-hourglass-start",
        "payments.refund": "fa-solid fa-undo",
        "payments.wallet": "fa-solid fa-wallet",
        "payments.wallettransaction": "fa-solid fa-receipt",
        "payments.paymentwebhook": "fa-solid fa-link",
        "voting": "fa-solid fa-vote-yea",
        "voting.votingevent": "fa-solid fa-chalkboard",
        "voting.votingcategory": "fa-solid fa-list-alt",
        "voting.candidate": "fa-solid fa-user",
        "voting.vote": "fa-solid fa-check-circle",
        "voting.votereligibility": "fa-solid fa-user-check",
        "voting.votingpayment": "fa-solid fa-file-invoice",
        "voting.votingresult": "fa-solid fa-trophy",
        "projects": "fa-solid fa-diagram-project",
        "projects.project": "fa-solid fa-folder-open",
        "projects.projectmember": "fa-solid fa-user-friends",
        "faculty": "fa-solid fa-chalkboard-user",
        "faculty.staff": "fa-solid fa-user-tie",
        "faculty.researcharea": "fa-solid fa-lightbulb",
        "history": "fa-solid fa-history",
        "history.record": "fa-solid fa-book",
        "history.societyhistory": "fa-solid fa-landmark",
        "history.historicalleader": "fa-solid fa-user-tie",
        "history.historicalmilestone": "fa-solid fa-award",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,
    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
    "use_google_fonts_cdn": True,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,
    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    # Add a language dropdown into the admin
    # "language_chooser": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
