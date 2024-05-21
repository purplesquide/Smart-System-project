import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import re

# Download NLTK resources if not already downloaded
nltk.download('punkt')
nltk.download('stopwords')

def extract_disease_data(disease_name, clinical_note):
    disease_patterns = {
        "heart": {
            "age": r"(\d+)\s*years?",
            "sex": r"(male|female)",
            "chest_pain_type": r"(typical angina|atypical angina|non-anginal pain|asymptomatic|absent)",
            "resting_blood_pressure": r"blood pressure:\s*(\d+)/(\d+)\s*mmHg",
            "cholesterol": r"cholesterol:\s*(\d+)\s*mg/dL",
            "glucose": r'glucose: (\d+)',
            "resting_ecg": r"resting ecg:\s*(normal|abnormal)",
            "max_heart_rate": r"max heart rate:\s*(\d+)\s*bpm",
            "exercise_angina": r"exercise-induced angina:\s*(yes|no|absent)",
            "oldpeak": r"oldpeak:\s*([0-9.]+)",
            "st_slope": r"st slope:\s*(upsloping|flat|downsloping)",
            "sex_age": r"(\d+)\s*years?,\s*(male|female)"
        },
        "diabetes": {
            "age": r"(\d+)\s*years?",
            "pregnancies": r'Pregnancies:\s*([^,\n]+)',
            "glucose": r'glucose: (\d+)',
            "blood_pressure": r'blood pressure: (\d+)/\d+',
            "skin_thickness": r'skin thickness: (\d+)',
            "insulin": r'insulin: (\d+)',
            "bmi": r'bmi: ([0-9.]+)',
            "diabetes_pedigree_function": r'diabetes pedigree function: ([0-9.]+)'
        }
    }

    mapping = {
        "sex": {"male": 1, "female": 0},
        "fasting_blood_sugar": {"normal": 0, "high": 1},
        "resting_ecg": {"normal": 0, "abnormal": 1},
        "exercise_angina": {"yes": 1, "no": 0, "absent": 0},
        "chest_pain_type": {
            "typical angina": 1,
            "atypical angina": 2,
            "non-anginal pain": 3,
            "asymptomatic": 4,
            "absent": 0
        },
        "st_slope": {"upsloping": 1, "flat": 2, "downsloping": 3}
    }

    extracted_values = []

    patterns = disease_patterns.get(disease_name.lower())
    if not patterns:
        return None

    for key, pattern in patterns.items():
        match = re.search(pattern, clinical_note, re.IGNORECASE)
        if match:
            if key == "sex_age":
                # Extracting both age and sex together
                age, sex = match.groups()
                extracted_values.append(int(age))
                extracted_values.append(sex.lower())
            else:
                value = match.group(1).strip()
                try:
                    value = int(value)  # Try converting to int
                except ValueError:
                    try:
                        value = float(value)  # Try converting to float
                    except ValueError:
                        value = value.lower()  # Convert to lowercase
                        if key in mapping and value in mapping[key]:
                            value = mapping[key][value]
                extracted_values.append(value)

    return extracted_values

if __name__ == "__main__":
    # Example clinical note (multiline string)
    clinical_note = """
    Patient: male, 38 years old
    - Pregnancies: 0
    - Glucose: 142 mg/dL
    - Blood Pressure: 125/82 mmHg
    - Skin Thickness: 32 mm
    - Insulin: 85 μU/mL
    - BMI: 29.0
    - Diabetes Pedigree Function: 0.85
    - Chest Pain Type: Typical Angina
    - Cholesterol: 205 mg/dL
    - Resting ECG: Abnormal
    - Max Heart Rate: 150 bpm
    - Exercise-Induced Angina: yes
    - Oldpeak: 2.0
    - ST Slope: Flat
    """

    if clinical_note:
        extracted_data = {
            "diabetes": [],
            "heart": []
        }

        for disease in ["diabetes", "heart"]:
            data = extract_disease_data(disease, clinical_note)
            if data:
                extracted_data[disease] = data

        if not any(extracted_data.values()):
            print("Error: No relevant information found in the clinical note.")
        else:
            diabetes_values = extracted_data["diabetes"]
            heart_values = extracted_data["heart"]

            # Process further as needed
            print("Diabetes values:", diabetes_values)
            print("Heart values:", heart_values)
