# "A 90-year-old patient presents with chest pain for 9 days, headache for 5 days, rash for 10 days, fatigue for 3 days, diarrhea for 10 days. Oxygen saturation is 96%, and body temperature is 100.4°F. Medical history includes asthma. Recent hospital stay.",Vitals-First with Comorbidity Overlay,Home care
# "A 34-year-old patient presents with dry cough for 1 days, rash for 2 days, diarrhea for 1 days, fatigue for 2 days. Oxygen saturation is 97%, and body temperature is 98.6°F. Medical history includes CHF, asthma. Recent hospital stay.",Symptom Cluster Then Escalation,Clinical judgment follow-up

import csv
import random

# --- Constants ---
vital_ranges = {
    'oxygen': [88, 90, 92, 94, 95, 96, 97, 98],
    'fever': [98.6, 99.5, 100.4, 101.2, 102.0, 103.0],
}
symptoms_pool = [
    "dry cough", "chest pain", "shortness of breath", "fatigue",
    "diarrhea", "headache", "fever", "nausea", "loss of smell", "rash"
]
comorbidities_pool = [
    "hypertension", "diabetes", "COPD", "asthma",
    "chronic kidney disease", "CHF", "HIV", "none"
]
exposures_pool = [
    "recent travel to outbreak area", "close contact with a sick relative",
    "recent hospital stay", "no known exposure", "recent travel abroad"
]
workflow_names = [
    "Vitals-First with Comorbidity Overlay",
    "Symptom Cluster Then Escalation",
    # "Duration-Weighted Symptom Score",
    # "Immunosuppression Priority Pathway",
    # ===
    # "Infection-Flag with Social Modifier",
    # "Exposure-Based Routing",
    # "Elderly-Centered Triage",
    # "Red Flag Rule Chain",
    # "Comorbidity-First Heuristic",
    # "Pediatric Guardrail Logic"
]


# --- Helper to Generate Case ---
def generate_case(workflow_name):
    age = random.randint(1, 90)
    symptoms = random.sample(symptoms_pool, k=random.randint(2, 5))
    durations = [f"{random.randint(1, 10)} days" for _ in symptoms]
    symptom_text = ', '.join(f"{s} for {d}" for s, d in zip(symptoms, durations))
    oxygen = random.choice(vital_ranges['oxygen'])
    fever = random.choice(vital_ranges['fever'])
    comorb_count = random.choices([0, 1, 2], weights=[0.3, 0.4, 0.3])[0]
    comorbidities = ["none"] if comorb_count == 0 else random.sample(comorbidities_pool, k=comorb_count)
    exposure = random.choice(exposures_pool)
    return {
        "Workflow": workflow_name,
        "Age": age,
        "Symptoms": symptom_text,
        "Oxygen Saturation": f"{oxygen}%",
        "Fever": f"{fever}°F",
        "Comorbidities": ', '.join(comorbidities),
        "Exposure or Travel History": exposure
    }

def parse_vitals(row): return int(row['Oxygen Saturation'][:-1]), float(row['Fever'][:-2])
def parse_comorbidities(row): return [] if row['Comorbidities'] == "none" else row['Comorbidities'].split(", ")

# --- Updated Evaluation Functions ---
def eval_vitals_comorbidity(row):
    oxygen, fever = parse_vitals(row)
    age = row['Age']
    comorb_count = len(parse_comorbidities(row))
    if oxygen < 92:
        severity = "critical"
    elif oxygen < 95 or fever > 101:
        severity = "moderate"
    else:
        severity = "mild"
    risk = "high" if comorb_count >= 2 or age >= 70 else "standard"
    if severity == "critical": return "ER referral"
    elif severity == "moderate" and risk == "high": return "Urgent clinical evaluation"
    elif severity == "moderate" and risk == "standard": return "Outpatient evaluation"
    else: return "Home care"

def eval_infection_social(row):
    _, fever = parse_vitals(row)
    exposure = row['Exposure or Travel History'].lower()
    social_flag = any(x in exposure for x in ["infants", "elderly", "immunocompromised"])
    infectious = fever >= 100.4
    if infectious and social_flag: return "Infectious disease referral"
    elif infectious: return "Outpatient evaluation"
    else: return "Home care"

def eval_symptom_cluster(row):
    symptoms = row['Symptoms'].lower()
    # Rule 1: Check for red flag symptoms
    red_flags = ["chest pain", "shortness of breath", "confusion"]
    if any(flag in symptoms for flag in red_flags):
        return "ER referral"
    # Rule 2: Check for viral cluster (fever + cough + fatigue)
    has_cluster = all(term in symptoms for term in ["fever", "cough", "fatigue"])
    # Extract symptom durations (e.g., "2 days", "1 days")
    durations = [int(word) for word in symptoms.split() if word.isdigit()]
    max_days = max(durations) if durations else 0
    # Rule 3: Decide based on cluster and duration
    if has_cluster and max_days >= 3:
        return "Outpatient evaluation"
    elif has_cluster:
        return "Home care"
    else:
        return "Clinical judgment follow-up"


def eval_exposure_routing(row):
    _, fever = parse_vitals(row)
    exposure = row['Exposure or Travel History'].lower()
    suspicious = "outbreak" in exposure or "contact" in exposure
    high_fever = fever >= 101.5
    if suspicious and high_fever: return "Infectious disease referral"
    elif high_fever: return "Outpatient evaluation"
    else: return "Home care"

def eval_elderly_triage(row):
    age = row['Age']
    symptoms = row['Symptoms']
    comorb_count = len(parse_comorbidities(row))
    if age >= 65 and any(flag in symptoms for flag in ["falls", "confusion", "incontinence", "delirium"]): return "Urgent clinical evaluation"
    if age >= 65 and comorb_count >= 2: return "Outpatient evaluation"
    return "Home care"

def eval_duration_score(row):
    symptoms = row['Symptoms']
    score = 0
    if "cough" in symptoms: score += 1
    if "fever" in symptoms: score += 1
    if "shortness of breath" in symptoms: score += 2
    max_duration = max([int(s) for s in symptoms.split() if s.isdigit()])
    if max_duration > 7: score += 1
    if score >= 4: return "Urgent clinical evaluation"
    elif score >= 2: return "Outpatient evaluation"
    else: return "Home care"

def eval_immuno_pathway(row):
    symptoms = row['Symptoms']
    comorbidities = row['Comorbidities'].lower()
    immuno = any(term in comorbidities for term in ["hiv", "steroid", "chemotherapy"])
    signs = any(sym in symptoms for sym in ["fever", "chills", "cough"])
    if immuno and signs: return "Urgent clinical evaluation"
    elif signs: return "Outpatient evaluation"
    else: return "Home care"

def eval_redflag_chain(row):
    symptoms = row['Symptoms']
    if any(x in symptoms for x in ["loss of consciousness", "seizure", "chest pain with exertion"]): return "ER referral"
    if any(x in symptoms for x in ["hematemesis", "melena", "severe abdominal pain"]): return "Urgent clinical evaluation"
    if any(x in symptoms for x in ["unexplained weight loss", "lymphadenopathy"]): return "Specialist consult"
    return "Home care"

def eval_comorbidity_heuristic(row):
    oxygen, fever = parse_vitals(row)
    status = "unstable" if fever >= 101 or oxygen < 94 else "stable"
    c = parse_comorbidities(row)
    high_risk = any(d in c for d in ["diabetes", "COPD", "CHF", "chronic kidney disease"])
    if high_risk and status == "unstable": return "ER referral"
    elif len(c) == 1 and status == "unstable": return "Urgent clinical evaluation"
    elif status == "stable": return "Outpatient evaluation"
    return "Home care"

def eval_pediatric_guardrail(row):
    age = row['Age']
    fever = float(row['Fever'].strip("°F"))
    symptoms = row['Symptoms']
    if any(k in symptoms for k in ["poor feeding", "lethargy", "inconsolable", "bulging fontanelle"]): return "ER referral"
    if age < 12 and fever > 100.4: return "Urgent clinical evaluation"
    return "Outpatient pediatric evaluation"

workflow_fn = {
    "Vitals-First with Comorbidity Overlay": eval_vitals_comorbidity,
    # "Infection-Flag with Social Modifier": eval_infection_social,
    "Symptom Cluster Then Escalation": eval_symptom_cluster,
    # "Exposure-Based Routing": eval_exposure_routing,
    # "Elderly-Centered Triage": eval_elderly_triage,
    "Duration-Weighted Symptom Score": eval_duration_score,
    "Immunosuppression Priority Pathway": eval_immuno_pathway,
    # "Red Flag Rule Chain": eval_redflag_chain,
    # "Comorbidity-First Heuristic": eval_comorbidity_heuristic,
    # "Pediatric Guardrail Logic": eval_pediatric_guardrail,
}

# Generate dataset
final_rows = []
for wf in workflow_names:
    for _ in range(10):
        row = generate_case(wf)
        answer = workflow_fn[wf](row)
        query = (
            f"A {row['Age']}-year-old patient presents with {row['Symptoms']}. "
            f"Oxygen saturation is {row['Oxygen Saturation']}, and body temperature is {row['Fever']}. "
            f"Medical history includes {row['Comorbidities']}. "
            f"{row['Exposure or Travel History'].capitalize()}."
        )
        final_rows.append({
            "query": query,
            "workflow": wf,
            "answer": answer
        })

# Save to CSV
output_path = "./triage_benchmark_dataset.csv"
with open(output_path, "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["query", "workflow", "answer"])
    writer.writeheader()
    writer.writerows(final_rows)

