# CSV Cleaner Pro 🧹

Clean, deduplicate, and transform CSV files in seconds. A Flask web app with Stripe payments.

## Features
- **Remove Duplicates** — Delete exact duplicate rows
- **Extract Emails** — Pull all email addresses from data
- **Clean Whitespace** — Remove extra spaces, trim cells
- **Fill Empty Cells** — Replace blanks with 'N/A'

## Stripe Integration
- Pay-per-use: $1.99/file (10-credit bundle: $19.90)
- Subscription: $9.99/month for unlimited cleaning
- Test mode keys in `.env`

## Deployment
```bash
pip install -r requirements.txt
# Set environment variables
export STRIPE_PUBLISHABLE_KEY=pk_test_...
export STRIPE_SECRET_KEY=sk_test_...
gunicorn app:app
```

## Stack
- Flask (Python)
- Stripe Checkout
- Gunicorn
- Deployed on Render/Hugging Face

## Live Demo
[Hugging Face Spaces](https://huggingface.co/spaces/edinsonmipc/csv-cleaner-pro)
