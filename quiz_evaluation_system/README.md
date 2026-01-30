# Quiz Evaluation System

Automated quiz answer evaluation using Azure OpenAI GPT-4o-mini.

## Features

- 🤖 AI-powered answer evaluation with nuanced scoring (0.0 to 1.0 scale)
- 📊 Batch processing of multiple quiz responses
- 🚨 Malpractice detection from tab switch events
- 📈 Comprehensive evaluation reports with statistics
- 💾 JSON output format for easy integration

## Setup

1. **Install dependencies:**
   ```bash
   cd quiz_evaluation_system
   pip install -r requirements.txt
   ```

2. **Configure Azure OpenAI:**
   - The system uses credentials from parent directory `.env` file
   - Or update `config.py` with your Azure OpenAI credentials

## Usage

### Test Mode (Single File)
Test the evaluation on one quiz response:
```bash
python3 evaluate_quiz_responses.py --test
```

### Batch Processing (All Files)
Evaluate all quiz responses in the directory:
```bash
python3 evaluate_quiz_responses.py --directory ../quiz_responses_20260128_142059
```

### Custom Output Directory
```bash
python3 evaluate_quiz_responses.py --directory ../quiz_responses_20260128_142059 --output my_results
```

## Output

The system generates:

1. **Individual evaluation files** (`eval_<bin_id>.json`):
   ```json
   {
     "bin_id": "...",
     "name": "Student Name",
     "email": "student@email.com",
     "scores": [1.0, 0.8, 0.5, ...],
     "total_score": 24.5,
     "max_score": 31.0,
     "percentage": 79.03,
     "tab_switch_count": 5,
     "malpractice_detected": true,
     "exited_quiz": false,
     "evaluation_timestamp": "2026-01-28T14:50:00"
   }
   ```

2. **Consolidated results** (`evaluation_results.json`): All evaluations in one file

3. **Summary statistics** (`summary.json`):
   - Average scores and percentages
   - Malpractice detection rate
   - Success/failure counts

## Scoring System

- **1.0**: Perfect answer, comprehensive and correct
- **0.7-0.9**: Correct but incomplete
- **0.4-0.6**: Partially correct
- **0.1-0.3**: Mostly incorrect but shows some understanding
- **0.0**: Wrong, irrelevant, or empty

## Malpractice Detection

Flags malpractice if:
- Tab switch count ≥ 4
- Event contains "malpractice_detected" warning
- Tracks if student exited quiz early
