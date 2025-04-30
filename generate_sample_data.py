import json
import uuid
import datetime
import random
import os
import pandas as pd
import numpy as np

# Ensure data directories exist
if not os.path.exists('data'):
    os.makedirs('data')

# Function to generate a unique survey ID
def generate_survey_id():
    return str(uuid.uuid4())

# Function to get the current timestamp
def get_current_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Sample business survey
def create_business_survey():
    survey_id = generate_survey_id()
    
    business_survey = {
        "title": "Business Performance and Customer Behavior Survey",
        "description": "This survey collects information about business performance and customer behavior to understand market trends and improve services.",
        "created_date": get_current_timestamp(),
        "questions": [
            {
                "id": "q1",
                "question_text": "What is your business type?",
                "type": "multiple_choice",
                "options": ["Retail", "Manufacturing", "Services", "Technology", "Healthcare", "Education", "Other"],
                "required": True
            },
            {
                "id": "q2",
                "question_text": "How many employees work at your company?",
                "type": "multiple_choice",
                "options": ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"],
                "required": True
            },
            {
                "id": "q3",
                "question_text": "What was your company's annual revenue in the last fiscal year?",
                "type": "multiple_choice",
                "options": ["Less than $100,000", "$100,000-$500,000", "$500,001-$1 million", "$1 million-$5 million", "$5 million-$10 million", "More than $10 million"],
                "required": True
            },
            {
                "id": "q4",
                "question_text": "How has your business performed compared to last year?",
                "type": "likert_scale",
                "scale_min": 1,
                "scale_max": 5,
                "scale_labels": ["Much worse", "Slightly worse", "About the same", "Slightly better", "Much better"],
                "required": True
            },
            {
                "id": "q5",
                "question_text": "Which customer acquisition channels are most effective for your business? (Select all that apply)",
                "type": "checkbox",
                "options": ["Social Media", "Email Marketing", "Search Engine Marketing", "Content Marketing", "Referrals", "Traditional Advertising", "Trade Shows", "Other"],
                "required": True
            },
            {
                "id": "q6",
                "question_text": "What is your average customer acquisition cost?",
                "type": "multiple_choice",
                "options": ["Less than $10", "$10-$50", "$51-$100", "$101-$500", "$501-$1000", "More than $1000"],
                "required": False
            },
            {
                "id": "q7",
                "question_text": "What is your customer retention rate?",
                "type": "multiple_choice",
                "options": ["Less than 20%", "21-40%", "41-60%", "61-80%", "81-100%"],
                "required": False
            },
            {
                "id": "q8",
                "question_text": "Rate the impact of the following factors on your customer buying decisions:",
                "type": "likert_scale",
                "scale_min": 1,
                "scale_max": 5,
                "scale_labels": ["No impact", "Low impact", "Moderate impact", "High impact", "Very high impact"],
                "required": True
            },
            {
                "id": "q9",
                "question_text": "What challenges is your business currently facing? (Select all that apply)",
                "type": "checkbox",
                "options": ["Finding new customers", "Retaining existing customers", "Price competition", "Market changes", "Technology adoption", "Staffing/HR issues", "Supply chain disruptions", "Regulatory compliance", "Financing/Cash flow"],
                "required": True
            },
            {
                "id": "q10",
                "question_text": "What is your expected business growth rate for the next year?",
                "type": "multiple_choice",
                "options": ["Negative growth", "0-5%", "6-10%", "11-20%", "21-50%", "More than 50%"],
                "required": True
            }
        ]
    }
    
    return survey_id, business_survey

# Sample customer satisfaction survey
def create_customer_satisfaction_survey():
    survey_id = generate_survey_id()
    
    customer_survey = {
        "title": "Customer Satisfaction and Product Feedback Survey",
        "description": "Help us improve our products and services by sharing your experience and feedback.",
        "created_date": get_current_timestamp(),
        "questions": [
            {
                "id": "q1",
                "question_text": "How did you hear about our products/services?",
                "type": "multiple_choice",
                "options": ["Search Engine", "Social Media", "Friend/Family", "Advertisement", "Blog/Article", "Other"],
                "required": True
            },
            {
                "id": "q2",
                "question_text": "How long have you been our customer?",
                "type": "multiple_choice",
                "options": ["Less than a month", "1-6 months", "6-12 months", "1-2 years", "More than 2 years"],
                "required": True
            },
            {
                "id": "q3",
                "question_text": "How often do you use our products/services?",
                "type": "multiple_choice",
                "options": ["Daily", "Weekly", "Monthly", "Quarterly", "Rarely"],
                "required": True
            },
            {
                "id": "q4",
                "question_text": "How would you rate your overall satisfaction with our products/services?",
                "type": "likert_scale",
                "scale_min": 1,
                "scale_max": 5,
                "scale_labels": ["Very dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very satisfied"],
                "required": True
            },
            {
                "id": "q5",
                "question_text": "What features do you value most in our products/services? (Select all that apply)",
                "type": "checkbox",
                "options": ["Quality", "Price", "Customer Service", "User Experience", "Features/Functionality", "Reliability", "Speed", "Other"],
                "required": True
            },
            {
                "id": "q6",
                "question_text": "How likely are you to recommend our products/services to others?",
                "type": "likert_scale",
                "scale_min": 0,
                "scale_max": 10,
                "scale_labels": ["0 - Not at all likely", "1", "2", "3", "4", "5 - Neutral", "6", "7", "8", "9", "10 - Extremely likely"],
                "required": True
            },
            {
                "id": "q7",
                "question_text": "What improvements would you suggest for our products/services?",
                "type": "paragraph",
                "required": False
            },
            {
                "id": "q8",
                "question_text": "How would you rate our customer service?",
                "type": "likert_scale",
                "scale_min": 1,
                "scale_max": 5,
                "scale_labels": ["Very poor", "Poor", "Average", "Good", "Excellent"],
                "required": False
            },
            {
                "id": "q9",
                "question_text": "Which of the following competitors have you used? (Select all that apply)",
                "type": "checkbox",
                "options": ["Competitor A", "Competitor B", "Competitor C", "Competitor D", "None of the above"],
                "required": False
            },
            {
                "id": "q10",
                "question_text": "May we contact you for follow-up questions?",
                "type": "multiple_choice",
                "options": ["Yes", "No"],
                "required": True
            }
        ]
    }
    
    return survey_id, customer_survey

# Generate sample responses for the business survey
def generate_business_responses(survey_id, count=50):
    responses = []
    
    business_types = ["Retail", "Manufacturing", "Services", "Technology", "Healthcare", "Education", "Other"]
    employee_counts = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
    revenue_ranges = ["Less than $100,000", "$100,000-$500,000", "$500,001-$1 million", "$1 million-$5 million", "$5 million-$10 million", "More than $10 million"]
    acquisition_channels = ["Social Media", "Email Marketing", "Search Engine Marketing", "Content Marketing", "Referrals", "Traditional Advertising", "Trade Shows", "Other"]
    acquisition_costs = ["Less than $10", "$10-$50", "$51-$100", "$101-$500", "$501-$1000", "More than $1000"]
    retention_rates = ["Less than 20%", "21-40%", "41-60%", "61-80%", "81-100%"]
    challenges = ["Finding new customers", "Retaining existing customers", "Price competition", "Market changes", "Technology adoption", "Staffing/HR issues", "Supply chain disruptions", "Regulatory compliance", "Financing/Cash flow"]
    growth_rates = ["Negative growth", "0-5%", "6-10%", "11-20%", "21-50%", "More than 50%"]
    
    # Weighted distribution for more realistic data
    business_weights = [0.3, 0.15, 0.2, 0.15, 0.1, 0.05, 0.05]
    employee_weights = [0.4, 0.3, 0.15, 0.08, 0.05, 0.02]
    revenue_weights = [0.25, 0.3, 0.2, 0.15, 0.07, 0.03]
    performance_weights = [0.1, 0.2, 0.3, 0.3, 0.1]  # Slightly better bias
    
    for i in range(count):
        # Timestamp with slight randomization to spread out responses
        days_ago = random.randint(0, 30)
        timestamp = (datetime.datetime.now() - datetime.timedelta(days=days_ago, 
                                                               hours=random.randint(0, 23), 
                                                               minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate response
        response = {
            "timestamp": timestamp,
            "q1": random.choices(business_types, weights=business_weights, k=1)[0],
            "q2": random.choices(employee_counts, weights=employee_weights, k=1)[0],
            "q3": random.choices(revenue_ranges, weights=revenue_weights, k=1)[0],
            "q4": random.choices(range(1, 6), weights=performance_weights, k=1)[0],
            "q5": random.sample(acquisition_channels, k=random.randint(1, 4)),
            "q6": random.choice(acquisition_costs) if random.random() > 0.1 else None,  # 10% skip rate
            "q7": random.choice(retention_rates) if random.random() > 0.15 else None,  # 15% skip rate
            "q8": random.randint(1, 5),
            "q9": random.sample(challenges, k=random.randint(1, 5)),
            "q10": random.choice(growth_rates)
        }
        
        responses.append(response)
    
    return responses

# Generate sample responses for the customer satisfaction survey
def generate_customer_responses(survey_id, count=75):
    responses = []
    
    sources = ["Search Engine", "Social Media", "Friend/Family", "Advertisement", "Blog/Article", "Other"]
    durations = ["Less than a month", "1-6 months", "6-12 months", "1-2 years", "More than 2 years"]
    frequencies = ["Daily", "Weekly", "Monthly", "Quarterly", "Rarely"]
    features = ["Quality", "Price", "Customer Service", "User Experience", "Features/Functionality", "Reliability", "Speed", "Other"]
    improvements = [
        "Your product could be more user-friendly.",
        "I would like to see more features related to analytics.",
        "Improve the mobile app experience.",
        "Faster customer service response times would be helpful.",
        "Lower prices would make your product more competitive.",
        "More customization options would be great.",
        "Better documentation and tutorials would help new users.",
        "Improve the search functionality."
    ]
    competitors = ["Competitor A", "Competitor B", "Competitor C", "Competitor D", "None of the above"]
    
    # Distribution weights for more realistic data
    source_weights = [0.35, 0.25, 0.2, 0.1, 0.05, 0.05]
    duration_weights = [0.15, 0.25, 0.3, 0.2, 0.1]
    frequency_weights = [0.3, 0.4, 0.2, 0.07, 0.03]
    
    for i in range(count):
        # Timestamp with slight randomization
        days_ago = random.randint(0, 45)  # Spread over 45 days
        timestamp = (datetime.datetime.now() - datetime.timedelta(days=days_ago, 
                                                               hours=random.randint(0, 23), 
                                                               minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Satisfaction generally follows a normal-ish distribution with slight positive bias
        satisfaction = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.1, 0.25, 0.4, 0.2], k=1)[0]
        
        # NPS score tends to correlate with satisfaction
        if satisfaction <= 2:
            nps_weights = [0.3, 0.25, 0.2, 0.15, 0.05, 0.03, 0.02, 0.0, 0.0, 0.0, 0.0]  # Detractors 
        elif satisfaction == 3:
            nps_weights = [0.05, 0.05, 0.1, 0.15, 0.2, 0.2, 0.15, 0.05, 0.03, 0.01, 0.01]  # Passives
        else:
            nps_weights = [0.0, 0.0, 0.0, 0.05, 0.05, 0.1, 0.15, 0.2, 0.2, 0.15, 0.1]  # Promoters
        
        nps_score = random.choices(range(11), weights=nps_weights, k=1)[0]
        
        # Customer service rating correlates with satisfaction
        cs_rating = max(1, min(5, satisfaction + random.randint(-1, 1)))
        
        # Generate response
        response = {
            "timestamp": timestamp,
            "q1": random.choices(sources, weights=source_weights, k=1)[0],
            "q2": random.choices(durations, weights=duration_weights, k=1)[0],
            "q3": random.choices(frequencies, weights=frequency_weights, k=1)[0],
            "q4": satisfaction,
            "q5": random.sample(features, k=random.randint(1, 4)),
            "q6": nps_score,
            "q7": random.choice(improvements) if random.random() > 0.3 else None,  # 30% skip rate
            "q8": cs_rating if random.random() > 0.2 else None,  # 20% skip rate
            "q9": random.sample(competitors, k=random.randint(0, 3)) if random.random() > 0.25 else None,  # 25% skip rate
            "q10": "Yes" if random.random() > 0.7 else "No"  # 70% say No
        }
        
        responses.append(response)
    
    return responses

# Create the surveys
surveys = {}
responses = {}

# Create and add business survey
business_survey_id, business_survey = create_business_survey()
surveys[business_survey_id] = business_survey
responses[business_survey_id] = generate_business_responses(business_survey_id, 50)

# Create and add customer satisfaction survey
customer_survey_id, customer_survey = create_customer_satisfaction_survey()
surveys[customer_survey_id] = customer_survey
responses[customer_survey_id] = generate_customer_responses(customer_survey_id, 75)

# Save the sample data
with open('surveys.json', 'w') as f:
    json.dump(surveys, f, indent=2)

with open('responses.json', 'w') as f:
    json.dump(responses, f, indent=2)

print(f"Sample data generated successfully:")
print(f"- Created 2 surveys")
print(f"- Generated {len(responses[business_survey_id])} responses for business survey")
print(f"- Generated {len(responses[customer_survey_id])} responses for customer satisfaction survey")
print("\nSurvey IDs for reference:")
print(f"- Business Survey ID: {business_survey_id}")
print(f"- Customer Survey ID: {customer_survey_id}")