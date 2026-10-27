"""MeaslesWatch BD: public health case study entry point."""

from measleswatch.dashboard import main

# Retain tested helpers used by the archived technical interface.
from measleswatch.legacy_dashboard import brief_outcome, reporting_calendar, yoy

if __name__ == "__main__":
    main()
