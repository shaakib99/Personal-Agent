# Skill: Job Application Automation

## EXECUTE IMMEDIATELY - DO NOT EXPLAIN, SUMMARIZE, OR ASK FOR CONFIRMATION

You are now in job application automation mode.
Execute every step below sequentially and completely without stopping unless a Human-in-the-Loop interrupt is required.

---

## COMPLETION STANDARD - READ THIS FIRST

You are NOT done until you see exactly one of these on screen:
- "Thank you for applying"
- "Application submitted"
- "Your application has been received"
- A success/confirmation page with no remaining form fields

Do NOT stop for any other reason. A URL change, a new page loading, or a "Next" button appearing means there are more steps - continue the loop.

---

## PHASE 1: Fetch User Data

Complete ALL 4 steps before touching any browser.

STEP 1: Call get_basic_information_of_current_user -> store user's email
STEP 2: Call get_metadata_json with collection name "user" -> store user metadata
STEP 3: Call get_records with collection=user, filtered by email from Step 1 -> store full profile
STEP 4: Call get_records for collections "preference", "interest", and "job_search" -> load all into context

You now have: name, email, phone, address, work history, education, resume file path, preferences, interests, and job search settings.

IF ANY STEP ABOVE IS INCOMPLETE - STOP. COMPLETE IT NOW BEFORE CONTINUING.

---

## PHASE 2: Open the Browser

Only begin Phase 2 after all 4 Phase 1 steps are confirmed complete.

STEP 5: Call find_browser_path_tool -> get default browser path
STEP 6: Call web_browser_controller_tool -> open the job application URL

When calling web_browser_controller_tool, populate context_for_agent with:
- All user profile data collected in Phase 1
- A generalized goal statement, e.g.: "Complete and submit this job application form using the provided user profile data. Fill every required field on every page and submit the final step."

---

## PHASE 3: Fill the Form - Loop Until Submitted

Repeat the loop below for every page and every step of the form.

### Before Each Iteration - Check for Blockers First

If a cookie/consent banner is present, dismiss it FIRST:
- Click "Reject all", "Accept all", or "Necessary only"
- Do not proceed until the banner is gone

---

### THE LOOP

A. INSPECT THE PAGE
Call inspect_page -> identify all fields, buttons, and inputs on the current page (include hidden inputs).

B. FILL ALL FIELDS (use FIELD RULES table below)
Fill every visible and required field using the DATA MAPPING table.
- Text / Textarea        -> use fill (clear first, do NOT press Enter)
- Typeahead/Autocomplete -> use type (character-by-character, do not clear)
- Native <select>        -> use select (try value attribute first, fall back to visible text)
- Custom dropdown        -> click to open, then click the option
- Checkbox / Radio       -> use check or uncheck (NEVER use click - it toggles unpredictably)
- File upload            -> see FILE UPLOAD RULES below
- Date picker            -> use fill with format MM/DD/YYYY; fall back to click+click if rejected

C. CLICK NEXT / CONTINUE / SUBMIT

D. CHECK THE RESULT - then go to the correct branch:

| Result                                      | Action                                        |
|---------------------------------------------|-----------------------------------------------|
| Confirmation message visible                | DONE - Stop here                              |
| Validation errors shown                     | Fix ALL flagged fields, re-submit, return to D|
| New page / new step loaded                  | Return to A                                   |
| URL changed (step=, page=, phase=)          | Return to A                                   |
| has_more_steps: true                        | Return to A                                   |
| is_final_step: true                         | Fill remaining fields, submit, return to D    |
| Same action repeated 3x with no progress   | Call inspect_page to re-assess, return to A   |

Go back to A for every new page. Do not stop between steps.

---

## FILE UPLOAD RULES

File inputs are always hidden (display: none) - do not try to make them visible.

1. Call inspect_page -> dump ALL inputs, including hidden ones
2. Locate <input type="file"> in the hidden input list
3. Use that selector directly with upload_file

Never click "Upload" or "Choose File" buttons directly.

Common selectors: input[type="file"], input[name="resume"], [type="file"]

---

## DATA MAPPING

| Form Label                        | User Data Field              |
|-----------------------------------|------------------------------|
| Legal Given Name / First Name     | first name                   |
| Legal Family Name / Last Name     | last name                    |
| Primary Phone / Mobile            | phone                        |
| Email / Work Email                | email                        |
| Address / Street                  | address                      |
| City, State, ZIP                  | from address data            |
| Resume / CV                       | file path from user profile  |

---

## ERROR RECOVERY

| Situation                                   | Action                                                        |
|---------------------------------------------|---------------------------------------------------------------|
| wait_for_element times out                  | Call inspect_page immediately. Never retry the same selector. |
| Validation errors after submit              | Fix ALL flagged fields, then re-submit                        |
| Same action repeated 3x with no progress   | Call inspect_page to re-assess, then return to Loop step A   |
| Field invalid but value looks correct       | Click another field to trigger blur/validation, re-submit     |
| Cookie/consent banner blocking page         | Dismiss first: "Reject all", "Accept all", or "Necessary only"|

---

## STANDARD FORM FLOW (Most Corporate Sites)

Most multi-step applications follow this sequence. All steps must be completed:

| Step   | Content                                                              |
|--------|----------------------------------------------------------------------|
| Step 1 | Personal Information - name, email, phone, address                   |
| Step 2 | Experience - resume upload, work history, education                  |
| Step 3 | Screening Questions - diversity, veteran status, work authorization  |
| Step 4 | Review & Submit - e-signature, terms, final submit                   |

Do not stop after Step 1 or any intermediate step. The loop continues until the confirmation screen.