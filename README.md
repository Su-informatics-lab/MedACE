# MedACE: Medical Agentic Concept Extraction

**MedACE** is a minimal proof‑of‑concept that demonstrates how to leverage **[AG2](https://github.com/ag2ai/ag2)** multi‑agent workflows to extract *immune‑related acute kidney injury (irAKI)* evidence from de‑identified clinical notes.

| Role                  | Description                                                                                                                           |
| --------------------- |---------------------------------------------------------------------------------------------------------------------------------------|
| **AKIExtractor**      | LLM agent that parses note bundles and produces a strict JSON record (ICI exposure → AKI events → management → outcome + confidence). |
| **ClinicianReviewer** | LLM (or human) agent that approves the JSON or requests fixes.                                                                        |
| **GroupChatManager**  | Orchestrates a round‑robin chat until the reviewer issues `APPROVE`.                                                                  |

---

## Quick start

```bash
# 1. install AG2 with OpenAI support
pip install "ag2[openai]"

# 2. set your key
export OPENAI_API_KEY="sk‑..." 

# 3. run the demo
python run.py 2      # 2 = classic irAKI example, 1 = non‑irAKI
```

You’ll see the full dialogue and the final JSON printed to the console.

---

## File overview

| File                          | Purpose                                                                  |
| ----------------------------- | ------------------------------------------------------------------------ |
| `run.py`                      | Defines prompts, agents, and group chat; contains two demo note bundles. |
| `requirements.txt` (optional) | Pin exact versions for reproducible runs.                                |

---

## Customising

* **Human‑in‑the‑loop review**: swap
  `clinician = AssistantAgent(...)` → `UserProxyAgent(...)`.
* **Real notes**: replace `load_demo_notes()` with your own loader.
* **Different schema**: edit the JSON template in `a_extractor_sys` and update the reviewer prompt.

---

## Contact

Questions or suggestions?
Open an [issue](https://github.com/your‑org/MedACE/issues) or email **Haining Wang** at hw56@iu.edu.

---

## License

MIT
