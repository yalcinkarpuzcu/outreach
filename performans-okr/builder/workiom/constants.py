"""
Workiom constants — field types, view types, trigger/action types, and color palette.
These map directly to the Workiom API enums.
"""


class F:
    """Field data types (dataType integer values)."""
    TEXT        = 0   # Plain string
    NUMBER      = 1   # Float
    DATE        = 2   # Send as "YYYY-MM-DD"
    BOOLEAN     = 3   # true / false
    SELECT      = 4   # Single select — requires options=["A","B"]
    LINK        = 5   # Relation (LinkList) — requires target_list or target_app+target_list
    USER        = 6   # Single user picker
    URL         = 7   # Website / URL string
    EMAIL       = 8   # Email string
    FILE        = 9   # File upload(s)
    PHONE       = 11  # Phone number string
    COUNT       = 12  # Auto-count of linked records
    CURRENCY    = 13  # Numeric, rendered as currency
    AUTONUMBER  = 14  # Auto-incrementing integer ID
    CHECKLIST   = 15  # Checklist items
    STATUS      = 16  # Status select (like SELECT but with status styling)
    MULTISELECT = 17  # Multi-select — requires options=["A","B"]
    MULTIUSER   = 18  # Multiple user pickers
    LOCATION    = 20  # Geographic location
    # Note: PROGRESSBAR (19) cannot be created via API — use NUMBER instead

    # Sentinel — not a real Workiom dataType. Builder resolves the actual
    # dataType from the source field on the linked list.
    LOOKUP      = "lookup"  # Lookup/projection field — needs via=<LINK field>, lookup_field=<field on linked list>


class LT:
    """List types (Lists/Create `type` integer)."""
    DATA    = 0   # Default — plain data list (watcher only)
    TASK    = 1   # Task list — auto status, dueDate, assignee, subtasks, parentTask
    PROCESS = 2   # Process list — auto title, status, assignee


class V:
    """View types (viewType integer values)."""
    GRID      = 0   # Default table/grid view
    KANBAN    = 1   # Kanban board — requires group_by field name
    CALENDAR  = 3   # Calendar — requires date_field name
    TIMELINE  = 4   # Timeline / Gantt-lite — requires date_field
    DOCUMENT  = 6   # Document / letter view — template in editorJsData
    PIVOT     = 7   # Pivot / summary table — requires group_by field
    MAP       = 8   # Map view — requires a LOCATION field
    GALLERY   = 10  # Card gallery
    ORG_CHART = 11  # Organization chart
    GANTT     = 12  # Full Gantt chart


class T:
    """Automation trigger types."""
    RECORD_CREATED = 0
    RECORD_UPDATED = 1
    TIME_TRIGGER   = 2
    RECURRING      = 3
    WEBHOOK        = 4
    RECORD_DELETED = 5


class A:
    """Automation action types."""
    CREATE_RECORD      = 0
    UPDATE_RECORD      = 1
    CONDITION          = 2   # internal wrapper — not shown in UI
    NOTIFY             = 3
    SEND_EMAIL         = 4   # basic Workiom email notification
    SEND_EMAIL_VIA     = 5   # email via integration (Gmail / Outlook / SMTP)
    #                    6   # Send SMS — type integer unconfirmed
    FIND_RECORDS       = 7
    #                    8   # Webhook — type integer unconfirmed
    # Note: CALL_API is type 9 in the actual API (not 8) — confirmed from live automations
    CALL_API           = 9
    APPROVAL           = 10
    DELETE_RECORD      = 11
    LOOP               = 12  # iterate over records in a list/view
    #                    13  # Move record — type integer unconfirmed
    #                    14  # Send Outlook (alt) — type integer unconfirmed
    AI_AGENT           = 15  # Workiom AI agent with knowledges + tools


class W:
    """Report widget types (widgetType integer values)."""
    NUMBER = 0   # KPI / number card — summaryMode: 0=count, 1=value
    BAR    = 1   # Bar chart (horizontal or vertical)
    PIE    = 2   # Pie / donut chart
    TABLE  = 4   # Data table


class AGG:
    """Report field aggregation types (fieldAggregationType integer values)."""
    SUM   = 0
    AVG   = 1
    MIN   = 2
    MAX   = 3
    COUNT = 4


class FREQ:
    """Date grouping frequency for reports (groupingDateFrequency integer values)."""
    DAY     = 0
    WEEK    = 1
    MONTH   = 2
    QUARTER = 3
    YEAR    = 4


# 9-color palette for select/status options (cycles automatically)
COLORS = [
    "#5bd77e",  # green
    "#f5c044",  # yellow
    "#ea346f",  # red/pink
    "#4e86f7",  # blue
    "#ffa979",  # orange
    "#ff86c7",  # pink
    "#8ed6ff",  # light blue
    "#5bd7d0",  # teal
    "#7942e3",  # purple
]


def color_for(index: int) -> str:
    """Return a palette color cycling through the 9-color set."""
    return COLORS[index % len(COLORS)]
