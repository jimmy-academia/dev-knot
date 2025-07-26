import csv
import random
import pandas as pd

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
    "Infection-Flag with Social Modifier",
    "Symptom Cluster Then Escalation",
    "Exposure-Based Routing",
    "Elderly-Centered Triage",
    "Duration-Weighted Symptom Score",
    "Immunosuppression Priority Pathway",
    "Red Flag Rule Chain",
    "Comorbidity-First Heuristic",
    "Pediatric Guardrail Logic"
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

# --- 10 Workflow Evaluation Functions ---
def eval_vitals_comorbidity(row):
    oxygen, fever = parse_vitals(row)
    age = row['Age']
    comorb_count = len(parse_comorbidities(row))
    severity = "critical" if oxygen < 92 else "moderate" if oxygen < 95 or fever > 101 else "mild"
    risk = "high" if comorb_count >= 2 or age >= 70 else "low"
    if severity == "critical": return "ER referral"
    if severity == "moderate" and risk == "high": return "Urgent clinical evaluation"
    if severity == "moderate" and risk == "low": return "Outpatient evaluation"
    return "Home care"

def eval_infection_social(row):
    _, fever = parse_vitals(row)
    infectious = fever >= 100.4
    social_flag = any(term in row['Exposure or Travel History'] for term in ["infants", "elderly", "immunocompromised"])
    if infectious and social_flag: return "Infectious disease referral"
    if infectious: return "Outpatient evaluation"
    return "Home care"

def eval_symptom_cluster(row):
    symptoms = row['Symptoms']
    if any(flag in symptoms for flag in ["chest pain", "shortness of breath", "confusion"]): return "ER referral"
    cluster = all(s in symptoms for s in ["fever", "cough", "fatigue"])
    days = max(int(word) for word in symptoms.split() if word.isdigit())
    if cluster and days < 3: return "Home care"
    if cluster and days >= 3: return "Outpatient evaluation"
    return "Clinical judgment follow-up"

def eval_exposure_routing(row):
    _, fever = parse_vitals(row)
    exposure = "outbreak" in row['Exposure or Travel History'] or "contact" in row['Exposure or Travel History']
    high_suspicion = fever >= 101.5 or "sudden" in row['Symptoms']
    if exposure and high_suspicion: return "Infectious disease referral"
    if high_suspicion: return "Outpatient evaluation"
    return "Home care"

def eval_elderly_triage(row):
    age = row['Age']
    geriatric_flags = any(symptom in row['Symptoms'] for symptom in ["falls", "confusion", "incontinence", "delirium"])
    comorb_count = len(parse_comorbidities(row))
    if age >= 65 and geriatric_flags: return "Urgent clinical evaluation"
    if age >= 65 and comorb_count >= 2: return "Outpatient evaluation"
    return "Home care"

def eval_duration_score(row):
    score = 0
    symptoms = row['Symptoms']
    if "cough" in symptoms: score += 1
    if "fever" in symptoms: score += 1
    if "shortness of breath" in symptoms: score += 2
    score += 1 if max([int(s) for s in symptoms.split() if s.isdigit()]) > 7 else 0
    return "Urgent clinical evaluation" if score >= 4 else "Outpatient evaluation" if score >= 2 else "Home care"

def eval_immuno_pathway(row):
    infection_signs = any(sym in row['Symptoms'] for sym in ["fever", "chills", "cough"])
    immuno = any(c in row['Comorbidities'] for c in ["HIV", "steroid", "chemotherapy"])
    if immuno and infection_signs: return "Urgent clinical evaluation"
    if infection_signs: return "Outpatient evaluation"
    return "Home care"

def eval_redflag_chain(row):
    s = row['Symptoms']
    if any(x in s for x in ["loss of consciousness", "seizure", "chest pain with exertion"]): return "ER referral"
    if any(x in s for x in ["hematemesis", "melena", "severe abdominal pain"]): return "Urgent clinical evaluation"
    if any(x in s for x in ["unexplained weight loss", "lymphadenopathy"]): return "Specialist consult"
    return "Home care"

def eval_comorbidity_heuristic(row):
    oxygen, fever = parse_vitals(row)
    status = "unstable" if fever >= 101 or oxygen < 94 else "stable"
    c = parse_comorbidities(row)
    score = "high" if any(d in c for d in ["diabetes", "COPD", "CHF", "chronic kidney disease"]) else "medium" if len(c) == 1 else "low"
    if score == "high" and status == "unstable": return "ER referral"
    if score == "medium" and status == "unstable": return "Urgent clinical evaluation"
    return "Outpatient evaluation" if status == "stable" else "Home care"

def eval_pediatric_guardrail(row):
    age = row['Age']
    fever = float(row['Fever'].strip("°F"))
    symptoms = row['Symptoms']
    red_flags = any(k in symptoms for k in ["poor feeding", "lethargy", "inconsolable", "bulging fontanelle"])
    if red_flags: return "ER referral"
    if age < 12 and fever > 100.4: return "Urgent clinical evaluation"
    return "Outpatient pediatric evaluation"

workflow_fn = {
    workflow_names[0]: eval_vitals_comorbidity,
    workflow_names[1]: eval_infection_social,
    workflow_names[2]: eval_symptom_cluster,
    workflow_names[3]: eval_exposure_routing,
    workflow_names[4]: eval_elderly_triage,
    workflow_names[5]: eval_duration_score,
    workflow_names[6]: eval_immuno_pathway,
    workflow_names[7]: eval_redflag_chain,
    workflow_names[8]: eval_comorbidity_heuristic,
    workflow_names[9]: eval_pediatric_guardrail,
}

# --- Main generation + evaluation ---
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

