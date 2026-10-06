# SALES

## Search locations and phone numbers

Search by city, pincode, or both. A pincode must contain 4–10 digits. Leads
without a phone number are included by default; choose **Phone numbers** in the
contact requirements to exclude businesses without a phone.

Examples:

```powershell
python main.py --city Kolkata --domain restaurant
python main.py --pincode 700075 --domain restaurant --require phone
python main.py --city Kolkata --pincode 700075 --domain restaurant
```

Reports include the business city and pincode when Google Places provides them,
and otherwise use the city or pincode supplied for the search.
# SALES
