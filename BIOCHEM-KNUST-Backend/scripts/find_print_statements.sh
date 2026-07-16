#!/bin/bash
#
# Search and Report Print Statements
# 
# This script finds all print() statements in Python files
# and generates a report for manual review and replacement.
#
# Usage:
#   chmod +x scripts/find_print_statements.sh
#   ./scripts/find_print_statements.sh
#

echo "=========================================="
echo "Searching for print() statements..."
echo "=========================================="
echo ""

# Search for print statements, exclude certain directories
grep -rn "print(" \
    --include="*.py" \
    --exclude-dir=migrations \
    --exclude-dir=__pycache__ \
    --exclude-dir=.git \
    --exclude-dir=venv \
    --exclude-dir=env \
    --exclude="*verify_logging.py" \
    --exclude="*logging_config.py" \
    . 2>/dev/null | while read -r line; do
    
    # Skip if it's in a comment
    if echo "$line" | grep -q "^\s*#"; then
        continue
    fi
    
    # Skip if it's in a docstring
    if echo "$line" | grep -q '"""'; then
        continue
    fi
    
    # Extract file and line number
    file=$(echo "$line" | cut -d: -f1)
    lineno=$(echo "$line" | cut -d: -f2)
    content=$(echo "$line" | cut -d: -f3-)
    
    echo "File: $file"
    echo "Line: $lineno"
    echo "Code: $content"
    echo ""
    echo "Suggested fix:"
    
    # Try to suggest a replacement
    if echo "$content" | grep -q "f\""; then
        # F-string print
        replacement=$(echo "$content" | sed 's/print(/logger.info(/')
        echo "  $replacement"
    elif echo "$content" | grep -q "Error\|error\|ERROR"; then
        replacement=$(echo "$content" | sed 's/print(/logger.error(/')
        echo "  $replacement"
    else
        replacement=$(echo "$content" | sed 's/print(/logger.info(/')
        echo "  $replacement"
    fi
    
    echo "----------------------------------------"
    echo ""
done

echo ""
echo "=========================================="
echo "Search Complete"
echo "=========================================="
echo ""
echo "To fix these issues:"
echo "1. Add logging import: import logging"
echo "2. Create logger: logger = logging.getLogger(__name__)"
echo "3. Replace print() with logger.info(), logger.error(), etc."
echo ""
echo "See LOGGING_QUICK_REFERENCE.md for examples"
echo ""
