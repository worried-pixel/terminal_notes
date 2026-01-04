# Terminal Notes - User Interface Screens

## Home Screen
```
============================================================================
                          TERMINAL NOTES ©
============================================================================

1. Create or Import a notebook
2. Quit

----------------------------------------------------------------------------
```
**First-time user experience** (no notebooks exist)

## Home Screen (with notebooks)
```
============================================================================
                          TERMINAL NOTES ©
============================================================================

1. List Notebooks (1 notebook, 3 notes, 2 files)
2. Create Notebook
3. Search Notes
4. Quit

----------------------------------------------------------------------------
```

## Notebook List Screen
```
============================================================================
                           Root Notebooks
============================================================================

[1] Work Notes (5 notes, 3 files, 2 subs)
[2] Personal (2 notes, 1 file)
[3] Projects (12 notes, 4 files, 1 sub)

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[C]reate  [V]iew  [D]elete  [B]ack
```

## Notebook View Screen (with content)
```
============================================================================
                     [1]Home/[2]Work Notes/
============================================================================

Notes & Files: (3 notes, 2 files)
[1] Meeting Notes 2024          [Updated: Dec 15 14:30]
[2] Q4 Planning                 [Updated: Dec 10 09:15]
[3] Budget Analysis.py          [Updated: Dec 05 16:45]
[4] Team Structure.md           [Updated: Nov 28 11:20]
[5] API Documentation           [Updated: Nov 25 13:10]

Sub-notebooks: (2 subs)
[6] View Sub-notebooks =>

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[N]ext  [C]reate  [V]iew  [J]ump  [D]elete  [B]ack  [Q]uit
```

## Notebook View Screen (empty)
```
============================================================================
                     [1]Home/[2]New Notebook/
============================================================================

This notebook is empty.
Create note, file or sub-notebook to get started!

----------------------------------------------------------------------------
[C]reate  [J]ump  [B]ack  [Q]uit
```

## Subnotebooks View Screen
```
============================================================================
              [1]Home/[2]Work Notes/ => 
============================================================================

Sub-notebooks of 'Work Notes' (2 subs):
[1] Client Projects (3 notes, 1 file)
[2] Internal (5 notes, 2 files, 1 sub)

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[C]reate  [V]iew  [J]ump  [D]elete  [B]ack  [Q]uit
```

## Note View Screen (regular note)
```
============================================================================
           [1]Home/[2]Work Notes/[3]Meeting Notes 2024
============================================================================

Note Title: Meeting Notes 2024
Created: Dec 10  Updated: Dec 15 14:30
----------------------------------------------------------------------------
Meeting with engineering team discussed Q4 deliverables
and timeline adjustments. The backend team needs two
additional weeks for the authentication system migration.

Frontend is on track but waiting on API specifications.
Design system updates will be deployed next Tuesday.

Action items:
1. John to provide updated API specs by Wednesday
2. Sarah to review migration plan
3. Team sync on Friday to align timelines

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[P]revious  [E]dit  [V]iew  [J]ump  [T]imeline  [R]ename  [B]ack  [Q]uit
```

## Note View Screen (file note with pagination)
```
============================================================================
          [1]Home/[2]Projects/[3]Budget Analysis.py
============================================================================

File Name: Budget Analysis.py [.py file]
Created: Dec 05  Updated: Dec 05 16:45
----------------------------------------------------------------------------
#!/usr/bin/env python3
# Budget Analysis Tool
# Version 2.1

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class BudgetAnalyzer:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        self.categories = self.data['category'].unique()
    
    def calculate_totals(self):
        monthly_totals = self.data.groupby('month')['amount'].sum()
        category_totals = self.data.groupby('category')['amount'].sum()
        
        return {
            'monthly': monthly_totals,
            'category': category_totals
        }
    
    def forecast_next_month(self):
        # Simple moving average forecast
        last_3_months = self.data[self.data['month'] >= 
                                 (datetime.now() - timedelta(days=90))]
        avg_spending = last_3_months['amount'].mean()
        
--- Page 1 of 3 ---

----------------------------------------------------------------------------
[N]ext  [E]dit  [V]iew  [J]ump  [T]imeline  [X]port  [R]ename  [B]ack  [Q]uit
```

## Search Options Screen
```
============================================================================
                            Search Notes
============================================================================

1. Quick Search (fast)
2. Comprehensive Search
3. Back

----------------------------------------------------------------------------
```

## Comprehensive Search Results Screen
```
============================================================================
               Search: 'budget' (7 matches)
============================================================================

[1] Budget Analysis.py (in Projects/)
[2] Q4 Budget Planning (in Work Notes/)
[3] Department Budgets (in Archive/)
[4] budget_2023.md (deleted from Work Notes/)
[5] Budget Meeting Notes (deleted from Meetings/)
[6] budget-template.xlsx (deleted from Templates/)
[7] Budget Review Q3 (in .../Finance/)

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[V]iew  [P]revious  [N]ext  [B]ack  [Q]uit
```

## Resurrected Note Screen
```
============================================================================
           Resurrected/ [RESURRECTED]
============================================================================

Note Title: Budget Meeting Notes
Status: Resurrected from Git history
----------------------------------------------------------------------------
Q2 Budget Review - May 15, 2023

Attendees: Finance team, department heads
Discussion focused on Q1 overspend in marketing
and IT infrastructure upgrades.

Approved items:
1. Marketing: $50K additional for Q2 campaign
2. IT: $120K for server upgrades (delayed from Q1)
3. HR: $25K for training programs

Action items to reduce spend in other areas...

--- Page 1 of 2 ---

----------------------------------------------------------------------------
[N]ext  [V]iew  [X]port  [T]imeline  [B]ack to search
```

## Historical Version Screen
```
============================================================================
          Historical/ [HISTORICAL VERSION: a1b2c3d4]
============================================================================

File Name: API Documentation [.md file]
Version from: 2023-10-15 11:30
----------------------------------------------------------------------------
# API Documentation v1.2
**DEPRECATED - See v2.0 docs**

## Endpoints

### GET /api/v1/users
Returns list of users with basic information.

### POST /api/v1/users
Create new user. Requires admin privileges.

### PUT /api/v1/users/:id
Update user information.

Note: This version will be discontinued on Dec 31, 2023.
Migrate to v2.0 endpoints as soon as possible.

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[V]iew  [X]port  [B]ack to timeline
```

## Timeline Results Screen
```
============================================================================
           Timeline for note: API Documentation
============================================================================

[1] 2023-12-15 14:30 EDITED (+3 lines, +45 words)
[2] 2023-11-20 09:15 EDITED (+10 lines, -25 words)
[3] 2023-10-15 11:30 CREATED (vim, 45 lines)
[4] 2023-10-10 16:45 RENAMED (api_spec.md → API Documentation)
[5] 2023-09-05 14:20 CREATED (internal, 12 lines)

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[V]iew  [B]ack
```

## Create Choice Screen
```
============================================================================
                    Create in: Work Notes
============================================================================

Choose what to create:
1 - Regular Note (internal/vim editor)
2 - Specialized File (.py, .html, .sh, etc.)
3 - Sub-notebook (nested container)

----------------------------------------------------------------------------
```

## File Creation Screen
```
============================================================================
           Create Specialized File in: Work Notes
============================================================================

Allowed extensions: html, js, css, ts, scss, vue, jsx, py, php, rb...

File name (with extension) [blank to cancel]: 

----------------------------------------------------------------------------
```

## Rename Screen
```
============================================================================
                       Rename Note
============================================================================

Current name: Budget Analysis.py
File extension: .py (will be kept)

New filename (without extension): 

----------------------------------------------------------------------------
```

## Export Screen
```
============================================================================
                   Export File: Budget Analysis.py
============================================================================

Enter export DIRECTORY (filename will be automatic):
Examples:
  /home/user/projects/
  ./exports/
  ../backup/

Recent export paths:
[1] /home/user/exports/
[2] ./backups/
[3] /tmp/

File will be saved as: Budget Analysis.py

Enter directory or number [1-3]: 

----------------------------------------------------------------------------
```

## Internal Editor Screen
```
============================================================================
                    Internal Editor
============================================================================

Enter your note. Press Ctrl+D on empty line when finished:
----------------------------------------------------------------------------
Current content (append below):
  This is existing content that will
  be appended to.

----------------------------------------------------------------------------
> 
```

## Search Notebook View (within search context)
```
============================================================================
               Work Notes/ (search)
============================================================================

Notes & Files:
[1] Meeting Notes 2024          [Updated: Dec 15 14:30]
[2] Budget Analysis.py          [Updated: Dec 05 16:45]
[3] API Documentation           [Updated: Nov 25 13:10]

--- Page 1 of 1 ---

----------------------------------------------------------------------------
[V]iew  [D]elete  [B]ack to search
```

## Resurrected Notebook Screen
```
============================================================================
        Client Projects/ [RESURRECTED]
============================================================================

Notes & Files:
[1] Project Scope.md            [Updated: Nov 10 09:15] [EMPTY]
[2] Requirements.docx           [Updated: Nov 05 14:30]
[3] Timeline.xlsx               [Updated: Nov 01 11:45]

Sub-notebooks:
[4] Design Assets (2 files)

----------------------------------------------------------------------------
[V]iew  [B]ack
```

## Jump Prompt Screen
```
============================================================================
               Jump Navigation
============================================================================

Jump to position j1, j2, j3, etc or 'b' to jump back:
Enter number or 'b': 

----------------------------------------------------------------------------
```

## Quit Confirmation
```
============================================================================
                    Quit Confirmation
============================================================================

Quit Terminal Notes? [y/N]: 

----------------------------------------------------------------------------
```

## Delete Confirmation
```
============================================================================
                    Delete Confirmation
============================================================================

Delete note 'Meeting Notes 2024'? [y/N]: 

----------------------------------------------------------------------------
```

## Import Notebook Screen
```
============================================================================
                    Import Existing Notebook
============================================================================

Enter path to Terminal Notes notebook:

Platform Examples:
  Linux/Mac: /home/user/projects/notes/
  Windows:   C:\Users\Name\Documents\notes\
  Relative:  ./my-notebook/ or ../shared-notes/

Notebook path: 

----------------------------------------------------------------------------
```

## Import Validation Screen
```
============================================================================
               Notebook Import Validation
============================================================================

Validating: /home/user/projects/notes/
────────────────────────────────────────────
 Path Accessibility... Validated
 File Structure... Validated
 Git Repository... Validated
 Data Format... Validated
 Duplicate Check... Validated

Importing notebook...

Notebook imported successfully!

----------------------------------------------------------------------------
Press Enter to continue...
```

## Create Notebook Screen
```
============================================================================
                    Create Notebook
============================================================================

Notebook name: 

Choose notebook location:
1. Default location (notebooks_root/)
2. Custom location (any folder on your system)

Choose [1-2]: 

----------------------------------------------------------------------------
```

## Custom Path Screen
```
============================================================================
               Custom Notebook Location
============================================================================

Enter full path for notebook folder:
Examples:
  /home/username/projects/notes/
  ~/Documents/work-notes/
  /tmp/temporary-notes/

Custom path: 

----------------------------------------------------------------------------
```
