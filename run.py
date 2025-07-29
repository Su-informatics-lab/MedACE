"""run.py
Module‑level docstring
Prototype AG2 team for extracting immune‑related acute kidney injury (irAKI) evidence
from clinical notes.

Usage
-----
$ OPENAI_API_KEY=... python run.py
The script loads a demo note bundle (replace with real text) and launches two agents:
1. AKIExtractor – extracts structured irAKI evidence.
2. ClinicianReviewer – critiques and approves or asks for revision.
"""

import os
import sys
from autogen import AssistantAgent, Team


# configuration
llm_config = {
    "model": os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16"),
    "api_key": os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE"),
    # "temperature": 0.3,
    "max_tokens": None,
    "context_window": None,  # remove any model-side context limit
}


# system prompt for the extraction assistant
a_extractor_sys = (
    "You are an NLP assistant specializing in phenotyping Immune‑Related Acute Kidney Injury (irAKI) from clinical notes. "
    "Follow KDIGO AKI definitions, ASCO / SITC immune‑toxicity guidelines, and the literature review provided. "
    "Your task is to read a bundle of notes for ONE patient and output a STRICT JSON object with the following schema:\n\n"
    "{\n"
    '  "ici_exposure": [            # ordered chronologically\n'
    '    {"drug": str, "start_date": YYYY-MM-DD, "stop_date": YYYY-MM-DD | null, "evidence": str}\n'
    "  ],\n"
    '  "aki_events": [              # KDIGO events sorted chronologically\n'
    '    {"event_date": YYYY-MM-DD, "kdigo_stage": 1|2|3, "creatinine_change_mg_dl": float, "evidence": str}\n'
    "  ],\n"
    '  "immune_attribution": [      # sentences linking AKI to ICI\n'
    '    {"sentence": str, "negated": bool}\n'
    "  ],\n"
    '  "management": {              # response to suspected irAKI\n'
    '    "ici_action": "Held"|"Discontinued"|"Continued"|"Unknown",\n'
    '    "steroids_started": bool,\n'
    '    "steroid_dose_mg_per_kg": float | null,\n'
    '    "biopsy_done": bool,\n'
    '    "biopsy_result": str | null,\n'
    '    "evidence": str\n'
    "  },\n"
    '  "outcome": {\n'
    '    "recovery_status": "Full"|"Partial"|"None"|"Unknown",\n'
    '    "dialysis": bool,\n'
    '    "latest_creatinine": float | null,\n'
    '    "evidence": str\n'
    "  },\n"
    '  "iraki_label": "Probable"|"Possible"|"Unlikely",  # based on extracted evidence\n'
    '  "confidence": float                 # 0.0–1.0 subjective confidence\n'
    "}\n\n"
    "Guidelines:\n"
    "1. Use ISO dates (YYYY‑MM‑DD). If only a month/year is present, approximate with the first of the month and add 'approx.' in evidence.\n"
    "2. Cite evidence snippets verbatim (<=200 chars) so reviewers can verify.\n"
    "3. Negations matter – exclude sentences like 'no immune nephritis'.\n"
    "4. Sort arrays chronologically. Output ONLY valid JSON with double quotes and NO trailing commas."
)

# system prompt for the clinician reviewer
clinician_sys = (
    "You are a senior nephrologist reviewing the assistant's JSON extraction. Check:\n"
    "• Clinical plausibility of KDIGO stages and timelines.\n"
    "• Correct causal attribution of AKI to ICI (evidence present, not negated).\n"
    "• Management actions are appropriate for the KDIGO stage.\n\n"
    "Respond with either:\n"
    "  APPROVE  – if all fields are correct and complete; or\n"
    "  REVISE   – followed by <=3 bullet points of required fixes."
)

# define agent
extractor = AssistantAgent(
    name="AKIExtractor",
    system_prompt=a_extractor_sys,
    llm_config=llm_config,
)

clinician = AssistantAgent(
    name="ClinicianReviewer",
    system_prompt=clinician_sys,
    llm_config=llm_config,
)

# group chat setup
team = Team(
    agents=[extractor, clinician],
    name="irAKI Phenotyping Team"
)


# duck note loader
def load_demo_notes(example: int = 2) -> str:
    """
    Returns two realistic, de-identified bundles of clinical notes
    for irAKI extraction demonstration. Set example=1 or 2.
    """
    # EXAMPLE 1: ESRD, falls, no ICI, not irAKI
    note_bundle_1 = (
        "ADMISSION HISTORY AND PHYSICAL"
        "ADMISSION DATE: 2024-08-29"
        "Reason for Admission: Recurrent falls"
        "History: 59-year-old male with IgD lambda MM (on daratumumab), meningioma, "
        "lambda light chain amyloidosis, acquired Factor X deficiency, ESRD on MWF dialysis, "
        "presented after fall. Recent labs: creatinine 5.01, baseline ESRD. No mention of immunotherapy. "
        "Assessment: ESRD, plan for regular dialysis. "
        "Physical therapy note: patient worked on transfers, no complaints of pain."
        "RADIOLOGY IMPRESSION (XR Pelvis 8/29/2024): No acute bony findings. Old fracture deformities noted."
    )

    # EXAMPLE 2: classic irAKI with ICI exposure
    note_bundle_2 = (
        "ONCOLOGY PROGRESS NOTE"
        "ENCOUNTER DATE: 2023-03-14"
        "History: 67-year-old female with metastatic melanoma started nivolumab on 2023-01-15. "
        "After 2 cycles, creatinine rose from 0.9 to 3.2 mg/dL. Nephrology consulted."
        "NEPHROLOGY CONSULT NOTE (2023-03-28): 'Acute kidney injury, likely related to immune checkpoint inhibitor therapy (nivolumab); "
        "KDIGO Stage 2; started methylprednisolone 1 mg/kg; nivolumab held.' "
        "Renal biopsy (2023-03-29): 'Interstitial nephritis consistent with ICI-associated AIN.'"
        "DISCHARGE SUMMARY (2023-04-10): 'Creatinine improved to 1.5, partial recovery; steroids tapered.'"
    )

    return note_bundle_1 if example == 1 else note_bundle_2


if __name__ == "__main__":
    # choose which note bundle to use: 1 = non-irAKI; 2 = classic irAKI
    try:
        example = int(sys.argv[1])
        assert example in [1, 2]
    except (IndexError, ValueError, AssertionError):
        print("Usage: python run.py [1|2]   # 1=non-irAKI, 2=classic irAKI (default: 2)")
        example = 2

    print(f"\n--- Running AG2 agentic extraction on example {example} ---\n")
    notes = load_demo_notes(example)

    # Team call: user asks question to team (triggers agent turn-taking)
    result = team.user_proxy().ask(
        f"Analyze the following note bundle and return irAKI JSON as instructed:\n{notes}"
    )

    # print the full team chat history
    for i, msg in enumerate(team.chat_history()):
        print(f"[Message {i}]\nRole: {msg['role']}\nContent:\n{msg['content']}\n")

    print("\n\nFinal output:\n", result)
