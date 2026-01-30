# 🚀 Automated Quiz Evaluation Pipeline

## Overview

This is a **single-command pipeline** that automates the entire quiz evaluation workflow from start to finish.

## What It Does

The pipeline performs these steps automatically:

1. **📋 Fetches bin IDs** from admin bin `6979e70643b1c97be951794c`
2. **📥 Downloads** quiz response data from each bin
3. **🤖 Evaluates** answers using Azure OpenAI LLM
4. **💾 Saves** individual evaluation JSONs to directory
5. **📊 Updates** consolidated `evaluation_results.json`
6. **📈 Appends** new results to Excel with malpractice highlighting

## Usage

### Run the Complete Pipeline

```bash
cd /media/supremology_2/New Volume/sandbox/Quiz_App-main
source venv/bin/activate
python3 evaluation_pipeline.py
```

That's it! One command does everything.

## What Gets Generated

### In `quiz_evaluation_system/evaluation_results_20260128_152329/`:

1. **Individual JSON files** - `eval_<bin_id>.json` for each submission
2. **Consolidated JSON** - `evaluation_results.json` with all evaluations
3. **Excel Report** - `evaluation_report.xlsx` (updated with new entries)
   - ✅ Automatically removes duplicates
   - 🔴 Red highlighting for malpractice cases
   - 📊 Sorted by percentage (best to worst)

## How Admin Tracking Works

### When Student Submits Quiz:

1. Quiz App creates a new bin for student answers
2. **Automatically** adds bin ID to admin bin with:
   - Student name
   - Email
   - Timestamp

### Modified File: `App.py`

Added these functions:
- `get_admin_bin()` - Retrieves current admin tracking data
- `add_bin_to_admin(bin_id, name, email)` - Adds new submission

## Admin Dashboard

View all tracked submissions:

```bash
python3 admin_dashboard.py
```

This shows:
- Total submissions
- Student names and emails
- Bin IDs
- Submission timestamps

Exports:
- `admin_submissions_list.json` - Full submission data
- `tracked_bin_ids.txt` - Just the bin IDs

## Pipeline Features

✅ **Smart Duplicate Handling** - Skips bins already evaluated  
✅ **Error Recovery** - Continues even if some bins fail  
✅ **Progress Tracking** - Shows [X/Y] progress for each bin  
✅ **Malpractice Detection** - Automatically flags suspicious activity  
✅ **Excel Formatting** - Red highlighting maintained when appending

## Example Output

```
🚀 Quiz Evaluation Pipeline - End to End Automation
================================================================================

📋 STEP 1: Fetching bin IDs from admin bin...
   ✅ Found 15 bin IDs in admin bin

📊 STEP 2-3: Downloading and evaluating 15 bins...

[1/15]
   📥 Processing bin: 6978a05fd0ea881f4089b009
      Student: John Doe
      Questions: 30
      🤖 Calling Azure OpenAI API...
      ✅ Score: 24.5/30.0 (81.67%)

[2/15]
   📥 Processing bin: 6978c0b1d0ea881f4089ff0e
      Student: Jane Smith
      Questions: 30
      🤖 Calling Azure OpenAI API...
      ✅ Score: 18.2/30.0 (60.67%)

...

================================================================================
Evaluation Summary:
   Total: 15
   Successful: 14
   Failed: 1
================================================================================

💾 Saved 15 evaluations to quiz_evaluation_system/evaluation_results_20260128_152329/

📊 STEP 4: Appending 15 new evaluations to Excel...
   ✅ Appended 15 new evaluations
   📁 Excel updated: quiz_evaluation_system/evaluation_results_20260128_152329/evaluation_report.xlsx

✨ Pipeline completed successfully!
```

## Workflow

### For New Quiz Submissions:

1. Students take quiz through web app
2. App automatically tracks bin IDs in admin bin
3. Run pipeline: `python3 evaluation_pipeline.py`
4. Get updated Excel with all evaluations

### Incremental Updates:

The pipeline is **idempotent** - you can run it multiple times:
- Only new bins are evaluated
- Existing evaluations are not duplicated
- Excel is updated with new entries only

## Files Modified/Created

### Modified:
- `App.py` - Added admin bin tracking on quiz submission

### Created:
- `evaluation_pipeline.py` - Main automated pipeline
- `admin_dashboard.py` - View tracked submissions
- `create_excel_report.py` - Excel generation script

## Requirements

Already installed in venv:
- `openai` - Azure OpenAI API
- `pandas` - Data manipulation
- `openpyxl` - Excel file handling
- `requests` - API calls

## Troubleshooting

**Issue**: 401 Unauthorized from Azure OpenAI  
**Fix**: Update Azure credentials in `quiz_evaluation_system/.env`

**Issue**: Admin bin empty  
**Fix**: Students must submit quiz through updated `App.py` for tracking

**Issue**: Excel file locked  
**Fix**: Close Excel before running pipeline
